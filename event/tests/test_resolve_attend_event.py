from django.contrib.auth.models import AnonymousUser
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event, EventAttendee
from user.models import User

class AttendEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.attendee1 = mixer.blend(User, email="attendee1@example.net")
        self.attendee2 = mixer.blend(User, email="attendee2@example.net")
        self.attendee3 = mixer.blend(User, email="attendee3@example.net")
        self.attendee4 = mixer.blend(User, email="attendee4@example.net")
        self.attendee5 = mixer.blend(User, email="attendee5@example.net")

        self.eventPublic = EventFactory(owner=self.attendee1,
                                        max_attendees=2)
        
        mixer.blend(
            EventAttendee,
            user=self.attendee1,
            event=self.eventPublic,
            state='accept'
        )

        self.mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "accept") {
                            edges {
                                name
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """


    def tearDown(self):
        super().tearDown()

    def test_attend_event_accept(self):

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'accept'
            }
        }

        self.graphql_client.force_login(self.attendee2)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 2)

    def test_attend_event_waitinglist(self):
        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "waitinglist") {
                            edges {
                                guid
                                name
                                email
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'waitinglist'
            }
        }

        mixer.blend(
            EventAttendee,
            user=self.attendee3,
            event=self.eventPublic,
            state='accept'
        )

        self.graphql_client.force_login(self.attendee2)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        guids = [r['guid'] for r in data["attendEvent"]["entity"]["attendees"]["edges"]]
        emails = [r['email'] for r in data["attendEvent"]["entity"]["attendees"]["edges"]]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertNotIn(str(self.attendee3.id), guids)
        self.assertIn(str(self.attendee2.id), guids)
        self.assertEqual([''], emails)

    def test_attend_event_from_accept_to_reject(self):

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'maybe'
            }
        }

        mixer.blend(
            EventAttendee,
            user=self.attendee2,
            event=self.eventPublic,
            state='accept'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee3,
            event=self.eventPublic,
            state='waitinglist'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee4,
            event=self.eventPublic,
            state='waitinglist'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee5,
            event=self.eventPublic,
            state='waitinglist'
        )

        self.graphql_client.force_login(self.attendee1)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 2)
        self.assertEqual(EventAttendee.objects.filter(event=self.eventPublic, user=self.attendee3, state='accept').count(), 1)

    def test_reject_event_with_subevent(self):
        subevent = mixer.blend(
            Event,
            parent=self.eventPublic,
        )

        sub_attendee = mixer.blend(
            EventAttendee,
            event=subevent,
            user=self.attendee1,
            state='accept'
        )

        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "reject") {
                            edges {
                                name
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'reject'
            }
        }

        self.graphql_client.force_login(self.attendee1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        sub_attendee.refresh_from_db()

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(sub_attendee.state, 'accept')

    def test_maybe_event_with_subevent(self):
        subevent = mixer.blend(
            Event,
            parent=self.eventPublic,
        )

        sub_attendee = mixer.blend(
            EventAttendee,
            event=subevent,
            user=self.attendee1,
            state='accept'
        )

        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "maybe") {
                            edges {
                                name
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'maybe'
            }
        }

        self.graphql_client.force_login(self.attendee1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        sub_attendee.refresh_from_db()

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(sub_attendee.state, 'accept')

    def test_maybe_disabled(self):
        self.disableMaybeEvent = EventFactory(
            owner=self.attendee1,
            max_attendees=2,
            enable_maybe_attend_event=False
        )

        variables = {
            "input": {
                "guid": self.disableMaybeEvent.guid,
                "state": 'maybe'
            }
        }

        self.graphql_client.force_login(self.attendee1)

        with self.assertGraphQlError("event_invalid_state"):
            self.graphql_client.post(self.mutation, variables)
