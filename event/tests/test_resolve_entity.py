from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event, EventAttendee
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE, ATTENDEE_ORDER_BY
from core.lib import datetime_isoformat
from django.utils.text import slugify


class EventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User, name="test_name2")
        self.user = mixer.blend(User)
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name="test_name3")
        self.today = timezone.now()

        self.eventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )
        self.subEventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None,
            parent=self.eventPublic
        )

        self.eventPrivate = Event.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            end_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=100,
            attend_event_without_account=True
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            user=self.user2,
            email=self.user2.email
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            name="test_name4",
            email='test@test4.nl'
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            name="test_name1",
            email='test@test.nl',
            checked_in_at=self.today
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            name="test_name3",
            user=self.authenticatedUser,
            email=self.authenticatedUser.email
        )

        EventAttendee.objects.create(
            event=self.eventPublic,
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
        self.eventPublic.delete()
        self.eventPrivate.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_event_anonymous(self):
        variables = {
            "guid": self.eventPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.eventPublic.guid)
        self.assertEqual(entity["title"], self.eventPublic.title)
        self.assertEqual(entity["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.eventPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.eventPublic.guid, slugify(self.eventPublic.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(entity["endDate"], None)
        self.assertEqual(entity["source"], self.eventPublic.external_link)
        self.assertEqual(entity["location"], self.eventPublic.location)
        self.assertEqual(entity["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(len(entity["attendees"]["edges"]), 0)
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity, None)

    def test_event_private(self):
        variables = {
            "guid": self.eventPrivate.guid,
            "orderBy": ATTENDEE_ORDER_BY.name
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.eventPrivate.guid)
        self.assertEqual(entity["title"], self.eventPrivate.title)
        self.assertEqual(entity["richDescription"], self.eventPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.eventPrivate.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.eventPrivate.guid, slugify(self.eventPrivate.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.eventPrivate.start_date)))
        self.assertEqual(entity["endDate"], str(datetime_isoformat(self.eventPrivate.end_date)))
        self.assertEqual(entity["source"], self.eventPrivate.external_link)
        self.assertEqual(entity["location"], self.eventPrivate.location)
        self.assertEqual(entity["rsvp"], self.eventPrivate.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.eventPrivate.attend_event_without_account)
        self.assertEqual(entity["attendees"]["edges"][0]["name"], 'test_name1')
        self.assertEqual(entity["attendees"]["edges"][0]["timeCheckedIn"], self.today.isoformat())
        self.assertEqual(entity["attendees"]["edges"][0]["url"], None)
        self.assertEqual(entity["attendees"]["edges"][0]["icon"], None)
        self.assertEqual(entity["attendees"]["edges"][0]["state"], 'accept')
        self.assertEqual(entity["attendees"]["edges"][1]["name"], 'test_name2')
        self.assertEqual(entity["attendees"]["edges"][1]["url"], self.authenticatedUser.url)
        self.assertEqual(entity["attendees"]["edges"][1]["icon"], self.authenticatedUser.icon)
        self.assertEqual(entity["attendees"]["edges"][1]["state"], 'accept')
        self.assertEqual(entity["attendees"]["edges"][2]["name"], 'test_name3')
        self.assertEqual(entity["attendees"]["edges"][3]["name"], 'test_name4')
        self.assertEqual(len(entity["attendees"]["edges"]), 4)

    def test_event_user(self):
        variables = {
            "guid": self.eventPublic.guid
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.eventPublic.guid)
        self.assertEqual(entity["title"], self.eventPublic.title)
        self.assertEqual(entity["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.eventPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/events/view/{}/{}".format(self.eventPublic.guid, slugify(self.eventPublic.title)))
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(entity["endDate"], None)
        self.assertEqual(entity["source"], self.eventPublic.external_link)
        self.assertEqual(entity["location"], self.eventPublic.location)
        self.assertEqual(entity["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(entity["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(entity["attendees"]["edges"][0]["name"], "test_name")
        self.assertEqual(entity["attendees"]["edges"][0]["email"], "")

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertIsNone(entity, None)

    def test_subevent_anonymous_user(self):
        variables = {
            "guid": self.subEventPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result['data']['entity']['guid'], self.subEventPublic.guid)

    def test_event_archived(self):
        self.eventPublic.is_archived = True
        self.eventPublic.save()

        variables = {
            "guid": self.eventPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.eventPublic.guid)
        self.assertEqual(entity["children"][0]["guid"], self.subEventPublic.guid)