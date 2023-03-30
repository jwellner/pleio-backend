from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.lib import early_this_morning
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import EventAttendee
from user.models import User


class EventsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        reference = early_this_morning() + timezone.timedelta(hours=12)

        tomorrow = reference + timezone.timedelta(days=1)
        yesterday = reference - timezone.timedelta(days=1)
        hours_ago_1 = reference - timezone.timedelta(hours=1)
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1)

        self.eventOneHourAgo = EventFactory(owner=self.user1,
                                            title="one hour ago (public)",
                                            start_date=hours_ago_1)

        self.eventFuture1 = EventFactory(owner=self.user1,
                                         title="future 1",
                                         start_date=tomorrow,
                                         read_access=[ACCESS_TYPE.logged_in])

        self.eventFuture2 = EventFactory(owner=self.user1,
                                         title="future 2 (public)",
                                         start_date=tomorrow + timezone.timedelta(hours=1))

        self.eventPast1 = EventFactory(owner=self.user1,
                                       title="past event (public)",
                                       start_date=yesterday)

        self.eventFutureGroup = EventFactory(owner=self.user1,
                                             title="future in group (public)",
                                             start_date=tomorrow,
                                             group=self.group)

        self.eventCurrentlyRunning = EventFactory(
            owner=self.user1,
            title="currently running (public)",
            start_date=yesterday,
            end_date=tomorrow,
        )

        self.query = """
            query EventsList($filter: EventFilter, $containerGuid: String, $offset: Int, $limit: Int) {
                events(filter: $filter, containerGuid: $containerGuid, offset: $offset, limit: $limit) {
                    total
                    edges {
                        guid
                        ...EventListFragment
                    }
                }
            }

            fragment EventListFragment on Event {
                guid
                title
                attendees {
                    total
                    edges {
                        email
                    }
                }
            }
        """

    def tearDown(self):
        self.eventFuture1.delete()
        self.eventFuture2.delete()
        self.eventFutureGroup.delete()
        self.eventPast1.delete()
        self.eventOneHourAgo.delete()
        self.eventCurrentlyRunning.delete()
        self.user1.delete()
        self.user2.delete()
        super().tearDown()

    @staticmethod
    def has_attendees(edges):
        for edge in edges:
            if edge['attendees'] and len(edge['attendees']['edges']) > 0:  # pragma: no cover
                return True
        return False

    @staticmethod
    def count_attendees(edges):
        total = 0
        for edge in edges:
            if 'attendees' in edge and 'total' in edge['attendees']:
                total = total + edge['attendees']['total']
        return total

    def test_events_anonymous(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "containerGuid": "1",  # Only get events on site level
            "filter": "upcoming"
        }

        mixer.blend(EventAttendee, user=self.user2, email=self.user2.email, event=self.eventFuture1, state='accept')
        mixer.blend(EventAttendee, user=None, event=self.eventFuture1, state='reject')
        mixer.blend(EventAttendee, user=self.user2, email=self.user2.email, event=self.eventFuture2, state='accept')
        mixer.blend(EventAttendee, user=None, event=self.eventFuture2, state='reject')

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["events"]["total"], 3)

        events = [edge['title'] for edge in data['events']['edges']]
        self.assertEqual(events, ['currently running (public)',
                                  'one hour ago (public)',
                                  'future 2 (public)'])

        self.assertEqual(data["events"]["edges"][2]["guid"], self.eventFuture2.guid)
        self.assertEqual(self.count_attendees(data['events']['edges']), 2)
        self.assertFalse(self.has_attendees(data['events']['edges']))

    def test_events_upcoming(self):
        variables = {
            "offset": 0,
            "containerGuid": "1",
            "filter": "upcoming"
        }

        # this is the first in upcoming list because it is still today.
        mixer.cycle(2).blend(EventAttendee, event=self.eventOneHourAgo, state='accept')

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]

        self.assertEqual(data["events"]["total"], 4)
        self.assertEqual(self.count_attendees(data["events"]["edges"]), 2)

        events = [edge['title'] for edge in data['events']['edges']]
        self.assertEqual(events, ['currently running (public)',
                                  'one hour ago (public)',
                                  'future 1',
                                  'future 2 (public)'])

    def test_events_previous(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "filter": "previous"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["events"]["total"], 1)

        events = [edge['title'] for edge in data['events']['edges']]
        self.assertEqual(events, ['past event (public)'])

    def test_events_no_filter(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "filter": ""
        }

        with self.assertGraphQlError(msg="Variable '$filter' got invalid value ''; Value '' does not exist in 'EventFilter' enum."):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.query, variables)

    def test_events_in_group(self):
        variables = {
            "limit": 20,
            "offset": 0,
            "containerGuid": self.group.guid
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["events"]["total"], 1)

    def test_events_no_subevent(self):
        EventFactory(owner=self.user1,
                     start_date=timezone.now() + timezone.timedelta(days=1),
                     parent=self.eventFuture2)

        variables = {
            "limit": 20,
            "offset": 0,
            "containerGuid": "1",
            "filter": "upcoming"
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["events"]["total"], 4)

        events = [edge['title'] for edge in data['events']['edges']]
        self.assertEqual(events, ['currently running (public)',
                                  'one hour ago (public)',
                                  'future 1',
                                  'future 2 (public)'])

    def test_without_mail_should_result_in_error(self):
        attendee = EventAttendee(
            event=self.eventFuture1,
            name="Test"
        )

        with self.assertRaises(ValidationError):
            attendee.save()
