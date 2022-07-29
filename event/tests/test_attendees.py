from django.core.exceptions import ValidationError
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event, EventAttendee
from event.tests.test_slots_available import create_slot
from user.factories import AdminFactory, UserFactory
from user.models import User
from django.http import HttpRequest
from django.utils import timezone
from ariadne import graphql_sync
from backend2.schema import schema
from core.constances import USER_ROLES, ATTENDEE_ORDER_BY, ORDER_DIRECTION


class AttendeesTestCase(FastTenantTestCase):

    def setUp(self):
        self.eventPublic = mixer.blend(Event)

        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])

        mixer.blend(
            EventAttendee,
            event=self.eventPublic,
            state='accept',
            name='Dd',
            email='Add@test.nl'
        )
        mixer.blend(
            EventAttendee,
            event=self.eventPublic,
            name='Ee',
            state='maybe',
            email='Aa@test.nl',
            checked_in_at=timezone.now()
        )
        mixer.blend(
            EventAttendee,
            event=self.eventPublic,
            state='maybe',
            name='Bb',
            email='Bb@test.nl'
        )
        mixer.blend(
            EventAttendee,
            event=self.eventPublic,
            state='accept',
            name='Cc',
            email='Bcc@test.nl',
            checked_in_at=(timezone.now() - timezone.timedelta(minutes=10))
        )

        self.query = """
            query EventQuery($guid: String, $offset: Int, $limit: Int, $orderBy: AttendeeOrderBy, $orderDirection: OrderDirection, $isCheckedIn: Boolean) {
                entity(guid: $guid) {
                    ... on Event {
                        attendees(offset: $offset, limit: $limit, orderBy: $orderBy, orderDirection: $orderDirection, isCheckedIn: $isCheckedIn) {
                            edges {
                                name
                                email
                            }
                            total
                            totalMaybe
                        }
                    }
                }
            }
        """

    def test_order_attendees_name(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "orderBy": ATTENDEE_ORDER_BY.name
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "Bb")
        self.assertEqual(data["entity"]["attendees"]["edges"][1]["name"], "Cc")
        self.assertEqual(data["entity"]["attendees"]["edges"][2]["name"], "Dd")
        self.assertEqual(data["entity"]["attendees"]["edges"][3]["name"], "Ee")

    def test_order_attendees_email(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "orderBy": ATTENDEE_ORDER_BY.email
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "Ee")

    def test_order_attendees_updated_at(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "orderBy": ATTENDEE_ORDER_BY.timeUpdated
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "Dd")

    def test_order_attendees_name_desc(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "orderBy": ATTENDEE_ORDER_BY.name,
            "orderDirection": ORDER_DIRECTION.desc
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "Ee")

    def test_checked_in_attendees(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "isCheckedIn": True
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual([d['name'] for d in data["entity"]["attendees"]["edges"]], ["Cc", "Ee"])

    def test_not_checked_in_attendees(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "isCheckedIn": False
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual([d['name'] for d in data["entity"]["attendees"]["edges"]], ['Bb', 'Dd'])


class TestAttendeesSigningUpForSubevents(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory()
        self.event = EventFactory(title="Parent event",
                                  owner=self.admin,
                                  start_date=timezone.now(),
                                  end_date=timezone.now() + timezone.timedelta(hours=8))

        self.slot1session1 = EventFactory(parent=self.event,
                                          title="Session 1",
                                          start_date=self.event.start_date)
        self.slot1session2 = EventFactory(parent=self.event,
                                          title="Session2 same time",
                                          start_date=self.slot1session1.start_date)
        self.slot2session1 = EventFactory(parent=self.event,
                                          title="Session 1",
                                          start_date=self.slot1session1.end_date)

        self.event.slots_available = [
            create_slot("Slot 1", self.slot1session1, self.slot1session2),
            create_slot("Slot 2", self.slot2session1)
        ]
        self.event.save()

        self.query = """
        query ParentEventQuery($guid: String) {
            entity(guid: $guid) {
                ... on Event {                
                    slotsAvailable {
                        name
                        alreadySignedUpInSlot
                    }
                }
            }
        }
        """
        self.variables = {
            'guid': self.event.guid
        }

    def test_allow_signup_for_multiple_sub_events_outside_slots(self):
        session1 = Event.objects.create(parent=self.event,
                                        title="Session 1",
                                        start_date=self.event.start_date,
                                        end_date=self.event.end_date)
        session2 = Event.objects.create(parent=self.event,
                                        title="Session2 same time",
                                        start_date=self.event.start_date,
                                        end_date=self.event.end_date)

        user = UserFactory(email='user@example.com')

        self.event.attendees.create(email=user.email, user=user, state='accept')

        session1.attendees.create(email=user.email, user=user, state='accept')
        session2.attendees.create(email=user.email, user=user, state='accept')

    def test_disallow_signup_for_multiple_sub_events_at_the_same_slot(self):
        user1 = UserFactory(name="User one")
        user2 = UserFactory(name="Another user")
        email1 = "User1@example.com"
        email2 = "User2@example.com"
        EventAttendee.objects.create(event=self.slot1session1,
                                     email=user1.email,
                                     user=user1,
                                     state="accept")
        EventAttendee.objects.create(event=self.slot1session1,
                                     email=email1,
                                     state="accept")

        # another user is allowed to signup.
        EventAttendee.objects.create(event=self.slot1session1,
                                     email=user2.email,
                                     user=user2,
                                     state="accept")
        EventAttendee.objects.create(event=self.slot1session1,
                                     email=email2,
                                     state="accept")

        # I am not allowed to signup for another session at the same slot.
        try:
            EventAttendee.objects.create(event=self.slot1session2,
                                         email=user1.email,
                                         user=user1,
                                         state="accept")
            self.fail("Unexpectedly not raising an exception for user at session %s" % self.slot1session2.title)
        except ValidationError as e:
            pass

        try:
            EventAttendee.objects.create(event=self.slot1session2,
                                         email=email1,
                                         state="accept")
            self.fail("Unexpectedly not raising an exception for email at session %s" % self.slot1session2.title)
        except ValidationError as e:
            pass

        # I am allowed to signup for a session at another block
        EventAttendee.objects.create(event=self.slot2session1,
                                     email=user1.email,
                                     user=user1,
                                     state="accept")
        EventAttendee.objects.create(event=self.slot2session1,
                                     email=email1,
                                     state="accept")

    def test_already_signed_up_in_slot(self):
        # Given.
        user1 = UserFactory(name="User one")
        user2 = UserFactory(name="Another user")

        # When.
        EventAttendee.objects.create(event=self.slot1session2,
                                     email=user1.email,
                                     user=user1,
                                     state="accept")

        # Then.
        self.graphql_client.force_login(user1)
        result = self.graphql_client.post(self.query, self.variables)
        self.assertTrue(result['data']['entity']['slotsAvailable'][0]['alreadySignedUpInSlot'])
        self.assertFalse(result['data']['entity']['slotsAvailable'][1]['alreadySignedUpInSlot'])

        self.graphql_client.force_login(user2)
        result = self.graphql_client.post(self.query, self.variables)
        self.assertFalse(result['data']['entity']['slotsAvailable'][0]['alreadySignedUpInSlot'])
        self.assertFalse(result['data']['entity']['slotsAvailable'][1]['alreadySignedUpInSlot'])
