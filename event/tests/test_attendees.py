from django.core.exceptions import ValidationError
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from event.models import Event, EventAttendee
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

    def test_disallow_signup_for_multiple_sub_events_at_the_same_slot(self):
        parentEvent = Event.objects.create(title="Parent event",
                                           owner=self.admin,
                                           start_date=timezone.now(),
                                           end_date=timezone.now() + timezone.timedelta(hours=8))
        slot1 = parentEvent.slots_available.create(name="slot1", index=0)
        slot2 = parentEvent.slots_available.create(name="slot2", index=1)
        slot1session1 = Event.objects.create(parent=parentEvent,
                                             slot=slot1,
                                             title="Session 1",
                                             start_date=parentEvent.start_date,
                                             end_date=parentEvent.start_date + timezone.timedelta(hours=2))
        slot1session2 = Event.objects.create(parent=parentEvent,
                                             slot=slot1,
                                             title="Session2 same time",
                                             start_date=slot1session1.start_date,
                                             end_date=slot1session1.end_date)
        slot2session1 = Event.objects.create(parent=parentEvent,
                                             slot=slot2,
                                             title="Session 1",
                                             start_date=slot1session1.end_date,
                                             end_date=slot1session1.end_date + timezone.timedelta(hours=2))

        user1 = mixer.blend(User, name="User one")
        user2 = mixer.blend(User, name="Another user")
        email1 = "User1@example.com"
        email2 = "User2@example.com"
        EventAttendee.objects.create(event=slot1session1,
                                     email=user1.email,
                                     user=user1,
                                     state="accept")
        EventAttendee.objects.create(event=slot1session1,
                                     email=email1,
                                     state="accept")

        # another user is allowed to signup.
        EventAttendee.objects.create(event=slot1session1,
                                     email=user2.email,
                                     user=user2,
                                     state="accept")
        EventAttendee.objects.create(event=slot1session1,
                                     email=email2,
                                     state="accept")

        # I am not allowed to signup for another session at the same slot.
        try:
            EventAttendee.objects.create(event=slot1session2,
                                         email=user1.email,
                                         user=user1,
                                         state="accept")
            self.fail("Unexpectedly not raising an exception for user at session %s" % slot1session2.title)
        except ValidationError as e:
            pass

        try:
            EventAttendee.objects.create(event=slot1session2,
                                         email=email1,
                                         state="accept")
            self.fail("Unexpectedly not raising an exception for email at session %s" % slot1session2.title)
        except ValidationError as e:
            pass

        # I am allowed to signup for a session at another block
        EventAttendee.objects.create(event=slot2session1,
                                     email=user1.email,
                                     user=user1,
                                     state="accept")
        EventAttendee.objects.create(event=slot2session1,
                                     email=email1,
                                     state="accept")
