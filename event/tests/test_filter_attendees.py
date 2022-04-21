from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from event.models import Event, EventAttendee
from user.models import User
from django.http import HttpRequest
from ariadne import graphql_sync
from backend2.schema import schema
from core.constances import USER_ROLES
from django.utils import timezone

class AttendeesTestCase(FastTenantTestCase):
    
    def setUp(self):
        self.eventPublic = mixer.blend(Event)
        self.today = timezone.now()
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])

        self.attendee1 = mixer.blend(User)
        self.attendee2 = mixer.blend(User)
        self.attendee3 = mixer.blend(User, name='Xx')
        self.attendee4 = mixer.blend(User)
        self.attendee5 = mixer.blend(User)

        mixer.blend(
            EventAttendee,
            user=self.attendee1,
            event=self.eventPublic,
            state='maybe',
            checked_in_at= self.today.isoformat()
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee2,
            event=self.eventPublic,
            state='maybe',
            name='Yy'
        )

        mixer.blend(
            EventAttendee,
            user=self.attendee3,
            event=self.eventPublic,
            state='accept',
            name='Xx'
        )

        self.query = """
            query EventQuery($guid: String, $offset: Int, $limit: Int, $query: String) {
                entity(guid: $guid) {
                    ... on Event {
                        attendees(offset: $offset, limit: $limit, query: $query) {
                            edges {
                                name
                                email
                            }
                            total
                            totalMaybe
                            totalAccept
                            totalGoing
                            totalCheckedIn
                        }
                    }
                }
            }
        """

    def tearDown(self):
        self.attendee1.delete()
        self.attendee2.delete()
        self.attendee3.delete()
        self.attendee4.delete()
        self.attendee5.delete()

    def test_query_attendees_get_all(self):

        request = HttpRequest()
        request.user = self.admin

        variables = {
            "guid": self.eventPublic.guid,
            "query": ""
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["total"], 3)
        self.assertEqual(data["entity"]["attendees"]["totalMaybe"], 2)
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 3)
        self.assertEqual(data["entity"]["attendees"]["totalCheckedIn"], 1)
        self.assertEqual(data["entity"]["attendees"]["totalGoing"], 0)


    def test_query_attendees_filter_name(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "query": "Xx",
            "guid": self.eventPublic.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["entity"]["attendees"]["total"], 3)
        self.assertEqual(data["entity"]["attendees"]["totalAccept"], 1)
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "Xx")