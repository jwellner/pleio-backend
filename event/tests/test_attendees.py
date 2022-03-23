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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual([d['name'] for d in data["entity"]["attendees"]["edges"]], ['Bb', 'Dd'])
