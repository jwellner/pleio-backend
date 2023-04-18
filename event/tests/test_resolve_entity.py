from django.utils import timezone
from django.utils.timezone import timedelta

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from user.factories import UserFactory
from event.models import Event, EventAttendee
from core.constances import ACCESS_TYPE, ATTENDEE_ORDER_BY
from core.lib import datetime_isoformat
from django.utils.text import slugify


class EventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticated_user = UserFactory(name="test_name2")
        self.user = UserFactory()
        self.user1 = UserFactory()
        self.user2 = UserFactory(name="test_name3")
        self.today = timezone.now()

        self.event_public = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user,
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )
        self.subevent_public = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user,
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None,
            parent=self.event_public
        )

        self.event_private = Event.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user,
            start_date=timezone.now(),
            end_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=100,
            attend_event_without_account=True
        )

        EventAttendee.objects.create(
            event=self.event_private,
            state='accept',
            user=self.user2,
            email=self.user2.email
        )

        EventAttendee.objects.create(
            event=self.event_private,
            state='accept',
            name="test_name4",
            email='test@test4.nl'
        )

        EventAttendee.objects.create(
            event=self.event_private,
            state='accept',
            name="test_name1",
            email='test@test.nl',
            checked_in_at=self.today
        )

        EventAttendee.objects.create(
            event=self.event_private,
            state='accept',
            name="test_name3",
            user=self.authenticated_user,
            email=self.authenticated_user.email
        )

        EventAttendee.objects.create(
            event=self.event_public,
            state='accept',
            name="test_name",
            email='test@test.nl'
        )

        self.query = """
            fragment EventParts on Event {
                title
                richDescription
                timeCreated
                timeUpdated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                startDate
                endDate
                location
                source
                rsvp
                isAttending
                location
                attendEventWithoutAccount
                attendees {
                    total
                    edges {
                        name
                        email
                        timeCheckedIn
                        url
                        icon
                        state
                    }
                }
                children {
                    guid
                }
                enableMaybeAttendEvent
            }
            query GetEvent($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...EventParts
                }
            }
        """

    def tearDown(self):
        self.event_public.delete()
        self.event_private.delete()
        self.authenticated_user.delete()
        super().tearDown()

    def test_event_anonymous(self):
        variables = {
            "guid": self.event_public.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.event_public.guid)
        self.assertEqual(entity["title"], self.event_public.title)
        self.assertEqual(entity["richDescription"], self.event_public.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.event_public.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.event_public.guid, slugify(self.event_public.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.event_public.start_date)))
        self.assertEqual(entity["endDate"], None)
        self.assertEqual(entity["source"], self.event_public.external_link)
        self.assertEqual(entity["location"], self.event_public.location)
        self.assertEqual(entity["rsvp"], self.event_public.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.event_public.attend_event_without_account)
        self.assertEqual(len(entity["attendees"]["edges"]), 0)
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])
        self.assertEqual(entity["enableMaybeAttendEvent"], self.event_public.enable_maybe_attend_event)

        variables = {
            "guid": self.event_private.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity, None)

    def test_event_private(self):
        variables = {
            "guid": self.event_private.guid,
            "orderBy": ATTENDEE_ORDER_BY.name
        }

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.event_private.guid)
        self.assertEqual(entity["title"], self.event_private.title)
        self.assertEqual(entity["richDescription"], self.event_private.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.event_private.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.event_private.guid, slugify(self.event_private.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.event_private.start_date)))
        self.assertEqual(entity["endDate"], str(datetime_isoformat(self.event_private.end_date)))
        self.assertEqual(entity["source"], self.event_private.external_link)
        self.assertEqual(entity["location"], self.event_private.location)
        self.assertEqual(entity["rsvp"], self.event_private.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.event_private.attend_event_without_account)
        self.assertEqual(entity["attendees"]["edges"][0]["name"], 'test_name1')
        self.assertEqual(entity["attendees"]["edges"][0]["timeCheckedIn"], self.today.isoformat())
        self.assertEqual(entity["attendees"]["edges"][0]["url"], None)
        self.assertEqual(entity["attendees"]["edges"][0]["icon"], None)
        self.assertEqual(entity["attendees"]["edges"][0]["state"], 'accept')
        self.assertEqual(entity["attendees"]["edges"][1]["name"], 'test_name2')
        self.assertEqual(entity["attendees"]["edges"][1]["url"], self.authenticated_user.url)
        self.assertEqual(entity["attendees"]["edges"][1]["icon"], self.authenticated_user.icon)
        self.assertEqual(entity["attendees"]["edges"][1]["state"], 'accept')
        self.assertEqual(entity["attendees"]["edges"][2]["name"], 'test_name3')
        self.assertEqual(entity["attendees"]["edges"][3]["name"], 'test_name4')
        self.assertEqual(len(entity["attendees"]["edges"]), 4)
        self.assertEqual(entity["enableMaybeAttendEvent"], self.event_private.enable_maybe_attend_event)

    def test_event_user(self):
        variables = {
            "guid": self.event_public.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.event_public.guid)
        self.assertEqual(entity["title"], self.event_public.title)
        self.assertEqual(entity["richDescription"], self.event_public.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.event_public.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.event_public.guid, slugify(self.event_public.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.event_public.start_date)))
        self.assertEqual(entity["endDate"], None)
        self.assertEqual(entity["source"], self.event_public.external_link)
        self.assertEqual(entity["location"], self.event_public.location)
        self.assertEqual(entity["rsvp"], self.event_public.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.event_public.attend_event_without_account)
        self.assertEqual(entity["attendees"]["edges"][0]["name"], "test_name")
        self.assertEqual(entity["attendees"]["edges"][0]["email"], "")
        self.assertEqual(entity["enableMaybeAttendEvent"], self.event_public.enable_maybe_attend_event)

        variables = {
            "guid": self.event_private.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertIsNone(entity, None)

    def test_subevent_anonymous_user(self):
        variables = {
            "guid": self.subevent_public.guid
        }

        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result['data']['entity']['guid'], self.subevent_public.guid)

    def test_event_archived(self):
        self.event_public.is_archived = True
        self.event_public.save()

        variables = {
            "guid": self.event_public.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.event_public.guid)
        self.assertEqual(entity["children"][0]["guid"], self.subevent_public.guid)


class TestResolveRangeEntityTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.now = timezone.now()
        self.authenticated_user = UserFactory()
        self.event = EventFactory(owner=self.authenticated_user,
                                  title="Limit instances to 10 items",
                                  start_date=self.now,
                                  end_date=self.now,
                                  range_starttime=self.now,
                                  range_settings={
                                      'type': 'dayOfTheWeek',
                                      'interval': 1,
                                      'instanceLimit': 10,
                                  })
        self.event2 = EventFactory(owner=self.authenticated_user,
                                   title="Limit instances until a specific date and time",
                                   start_date=self.now,
                                   end_date=self.now,
                                   range_starttime=self.now,
                                   range_ignore=True,
                                   range_settings={
                                       'type': 'dayOfTheWeek',
                                       'interval': 2,
                                       'repeatUntil': (self.now + timedelta(days=15)).isoformat()
                                   })
        self.query = """
        query EntityQuery($guid: String
                          $guid2: String
                          $yesterday: DateTime
                          $tomorrow: DateTime
                          $nextWeek: DateTime
                          $nextMonth: DateTime) {
            entity(guid: $guid) {
                ... on Event {
                    guid
                    rangeSettings {
                        isIgnored
                        type
                        interval
                        repeatUntil
                        instanceLimit
                        
                        nextEvent {
                            guid
                        }
                        yesterday: nextEvent(timeAfter: $yesterday) {
                            guid
                        }
                        tomorrow: nextEvent(timeAfter: $tomorrow) {
                            guid
                        }
                        nextWeek: nextEvent(timeAfter: $nextWeek) {
                            guid
                        }
                        nextMonth: nextEvent(timeAfter: $nextMonth) {
                            guid
                        }
                    }
                }
            }
            entity2: entity(guid: $guid2) {
                ... on Event {
                    guid
                    rangeSettings {
                        isIgnored
                        type
                        interval
                        repeatUntil
                        instanceLimit
                        nextEvent {
                            guid
                            rangeSettings {
                                isIgnored
                            }
                        }
                    }
                }
            }
        }
        """
        self.variables = {
            'guid': self.event.guid,
            'guid2': self.event2.guid,
            'yesterday': (self.now + timedelta(days=-1)).isoformat(),
            'tomorrow': (self.now + timedelta(days=1)).isoformat(),
            'nextWeek': (self.now + timedelta(days=7)).isoformat(),
            'nextMonth': (self.now + timedelta(days=31)).isoformat(),
        }

    def test_range_entity(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, self.variables)

        # PART 1a: Test the content of the first event
        entity = result['data']['entity']
        range_settings = entity['rangeSettings']
        self.assertEqual(entity['guid'], self.event.guid)
        self.assertEqual(range_settings['isIgnored'], False)
        self.assertEqual(range_settings['type'], 'dayOfTheWeek')
        self.assertEqual(range_settings['interval'], 1)
        self.assertEqual(range_settings['instanceLimit'], 10)

        # PART 2: Test the nextEvent functionality
        next = range_settings['nextEvent']
        self.assertEqual(range_settings['yesterday']['guid'], next['guid'])
        self.assertEqual(range_settings['tomorrow']['guid'], next['guid'])

        all_until_tested = [entity['guid']]
        self.assertNotIn(range_settings['nextEvent']['guid'], all_until_tested)

        all_until_tested.append(next['guid'])
        self.assertNotIn(range_settings['nextWeek']['guid'], all_until_tested)

        all_until_tested.append(range_settings['nextWeek']['guid'])
        self.assertNotIn(range_settings['nextMonth']['guid'], all_until_tested)

        # PART 1b: Test the content of the second event.
        entity2 = result['data']['entity2']
        entity21 = Event.objects.get_range_after(self.event2).first()
        range_settings = entity2['rangeSettings']
        self.assertEqual(entity2['guid'], self.event2.guid)
        self.assertEqual(range_settings, {
            'isIgnored': True,
            'type': 'dayOfTheWeek',
            'interval': 2,
            'repeatUntil': self.event2.range_settings['repeatUntil'],
            'instanceLimit': None,
            'nextEvent': {
                'guid': entity21.guid,
                'rangeSettings': {
                    'isIgnored': False,
                }
            }
        })
