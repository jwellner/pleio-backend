from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.models import Event, EventAttendee
from user.models import User
from core.constances import USER_ROLES, ACCESS_TYPE
from django.utils import timezone


class AttendeesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.eventPublic = mixer.blend(Event,
                                       read_access=[ACCESS_TYPE.public])
        self.today = timezone.now()
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])

        self.attendee1 = mixer.blend(User, email='accept@checkedin.net', name="Peter Accept CI")
        self.attendee2 = mixer.blend(User, email='accept@notcheckedin.net', name="John Accept")
        self.attendee3 = mixer.blend(User, email='waiting@checkedin.net', name="Suzan Waitinglist CI")
        self.attendee4 = mixer.blend(User, email='waiting@notcheckedin.net', name="Cathy Waitinglist")
        self.attendee5 = mixer.blend(User, email="maybe@example.net", name="Veronica Maybe")
        self.attendee6 = mixer.blend(User, email="reject@example.net", name="Repelsteeltje Reject")

        mixer.blend(EventAttendee,
                    user=self.attendee1,
                    event=self.eventPublic,
                    state='accept',
                    checked_in_at=self.today.isoformat())
        mixer.blend(EventAttendee,
                    user=self.attendee2,
                    event=self.eventPublic,
                    state='accept')
        mixer.blend(EventAttendee,
                    user=self.attendee3,
                    event=self.eventPublic,
                    state='waitinglist',
                    checked_in_at=self.today.isoformat())
        mixer.blend(EventAttendee,
                    user=self.attendee4,
                    event=self.eventPublic,
                    state='waitinglist')
        mixer.blend(EventAttendee,
                    user=self.attendee5,
                    event=self.eventPublic,
                    state='maybe')
        mixer.blend(EventAttendee,
                    user=self.attendee6,
                    event=self.eventPublic,
                    state='reject')

        self.query = """
            query EventQuery($guid: String, $offset: Int, $limit: Int, $query: String) {
                entity(guid: $guid) {
                    ... on Event {
                        attendees(offset: $offset, limit: $limit, query: $query) {
                            edges {
                                name
                                email
                                state
                                timeCheckedIn
                            }
                            total

                            totalCheckedIn
                            totalAccept
                            totalAcceptNotCheckedIn
                            totalWaitinglist
                            totalWaitinglistNotCheckedIn
                          
                            totalMaybe
                            totalReject
                        }
                    }
                }
            }
        """

    def test_query_attendees_get_all(self):
        variables = {
            "guid": self.eventPublic.guid,
            "query": ""
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 6)
        self.assertEqual(data["entity"]["attendees"]["total"], 6)
        self.assertEqual(data["entity"]["attendees"]["totalCheckedIn"], 2)

        self.assertEqual(data["entity"]["attendees"]["totalAccept"], 2)
        self.assertEqual(data["entity"]["attendees"]["totalAcceptNotCheckedIn"], 1)
        self.assertEqual(data["entity"]["attendees"]["totalWaitinglist"], 2)
        self.assertEqual(data["entity"]["attendees"]["totalWaitinglistNotCheckedIn"], 1)

        self.assertEqual(data["entity"]["attendees"]["totalMaybe"], 1)
        self.assertEqual(data["entity"]["attendees"]["totalReject"], 1)

    def test_query_attendees_filter_name(self):
        variables = {
            "query": "Peter",
            "guid": self.eventPublic.guid
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["attendees"]["total"], 1)
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], self.attendee1.name)

    def test_unauthenticated_hides_protected_info(self):
        result = self.graphql_client.post(self.query, {"guid": self.eventPublic.guid})

        data = result["data"]
        # Available:
        self.assertEqual(data['entity']['attendees']['total'], 6)
        self.assertEqual(data['entity']['attendees']['totalAccept'], 2)
        self.assertEqual(data['entity']['attendees']['totalWaitinglist'], 2)

        # Hidden:
        self.assertEqual(data['entity']['attendees']['edges'], [])
        self.assertEqual(data['entity']['attendees']['totalCheckedIn'], None)
        self.assertEqual(data['entity']['attendees']['totalAcceptNotCheckedIn'], None)
        self.assertEqual(data['entity']['attendees']['totalWaitinglistNotCheckedIn'], None)
        self.assertEqual(data['entity']['attendees']['totalMaybe'], None)
        self.assertEqual(data['entity']['attendees']['totalReject'], None)
