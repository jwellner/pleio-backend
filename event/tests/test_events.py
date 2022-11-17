from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import EventAttendee
from user.models import User


class EventsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        tomorrow = timezone.now() + timezone.timedelta(days=1)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        hours_ago_1 = timezone.now() - timezone.timedelta(hours=1)
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1)

        self.eventOneHourAgo = EventFactory(owner=self.user1,
                                            start_date=hours_ago_1)

        self.eventFuture1 = EventFactory(owner=self.user1,
                                         start_date=tomorrow,
                                         read_access=[ACCESS_TYPE.logged_in])

        self.eventFuture2 = EventFactory(owner=self.user1,
                                         start_date=tomorrow)

        self.eventPast1 = EventFactory(owner=self.user1,
                                         start_date=yesterday)

        self.eventFutureGroup = EventFactory(owner=self.user1,
                                         start_date=tomorrow,
                                         group=self.group)

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
                    excerpt
                    url
                    votes
                    hasVoted
                    isBookmarked
                    inGroup
                    canBookmark
                    tags
                    rsvp
                    isFeatured
                    featured {
                        image
                        video
                        videoTitle
                        positionY
                    }
                    startDate
                    endDate
                    location
                    timeCreated
                    commentCount
                    comments {
                        guid
                        richDescription
                        timeCreated
                        canEdit
                        hasVoted
                        votes
                        owner {
                        guid
                        username
                        name
                        icon
                        url
                        }
                    }
                    owner {
                        guid
                        username
                        name
                        url
                        icon
                    }
                    attendees(limit: 1) {
                        total
                        edges {
                        email
                        name
                        icon
                        }
                    }
                    group {
                        guid
                        ... on Group {
                        name
                        url
                        membership
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
        self.user1.delete()
        self.user2.delete()
        super().tearDown()

    def test_events_anonymous(self):

        variables = {
            "limit": 20,
            "offset": 0,
            "containerGuid": "1", # Only get events on site level
            "filter": "upcoming"
        }

        mixer.blend(EventAttendee, user=self.user2, email=self.user2.email, event=self.eventFuture1, state='accept')
        mixer.blend(EventAttendee, user=None, event=self.eventFuture1, state='reject')
        mixer.blend(EventAttendee, user=self.user2, email=self.user2.email, event=self.eventFuture2, state='accept')
        mixer.blend(EventAttendee, user=None, event=self.eventFuture2, state='reject')

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["events"]["total"], 2)
        self.assertEqual(data["events"]["edges"][1]["guid"], self.eventFuture2.guid)
        self.assertEqual(data["events"]["edges"][1]["attendees"]["total"], 2)
        self.assertEqual(len(data["events"]["edges"][0]["attendees"]["edges"]), 0)

    def test_events_upcoming(self):

        variables = {
            "limit": 1,
            "offset": 0,
            "containerGuid": "1",
            "filter": "upcoming"
        }

        # this is the first in upcoming list because it is still today.
        mixer.cycle(2).blend(EventAttendee, event=self.eventOneHourAgo, state='accept')

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]

        self.assertEqual(data["events"]["total"], 3)
        self.assertEqual(data["events"]["edges"][0]["attendees"]["total"], 1)

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

        subevent = EventFactory(owner=self.user1,
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

        self.assertEqual(data["events"]["total"], 3)
        self.assertTrue(subevent.guid not in [d['guid'] for d in data["events"]["edges"]])

    def test_without_mail_should_result_in_error(self):
        attendee = EventAttendee(
            event=self.eventFuture1,
            name="Test"
        )

        with self.assertRaises(ValidationError):
            attendee.save()
