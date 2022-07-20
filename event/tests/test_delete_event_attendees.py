from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event, EventAttendee
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest import mock


class DeleteEventAttendeesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.attendee_user = mixer.blend(User)
        self.owner = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.event = mixer.blend(Event)
        self.event.owner = self.owner
        self.event.read_access = [ACCESS_TYPE.public]
        self.event.write_access = [ACCESS_TYPE.user.format(self.owner.id)]
        self.event.attend_event_without_account = True
        self.event.save()

        EventAttendee.objects.create(
            event=self.event,
            user=self.attendee_user,
            email=self.attendee_user.email
        )
        EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test1@test.nl"
        )
        EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test2@test.nl"
        )

    @mock.patch('event.resolvers.shared.submit_delete_event_attendees_mail')
    def test_delete_attendees_from_event_by_admin(self, mocked_send_mail):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.attendee_user.email]
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.event.refresh_from_db()
        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(mocked_send_mail.call_count, 2)

    @mock.patch('event.resolvers.shared.submit_delete_event_attendees_mail')
    def test_delete_attendees_from_event_by_owner(self, mocked_send_mail):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.attendee_user.email]
            }
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.event.refresh_from_db()
        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(mocked_send_mail.call_count, 2)

    @mock.patch('event.mail_builders.delete_event_attendees.submit_delete_event_attendees_mail')
    def test_delete_attendees_from_event_by_user(self, mocked_send_mail):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.attendee_user.email]
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.attendee_user)
            self.graphql_client.post(mutation, variables)

    def test_delete_attendees_from_event_with_subevent(self):
        subevent = mixer.blend(Event,
                               parent=self.event
                               )

        mixer.blend(EventAttendee,
                    user=self.attendee_user,
                    event=subevent
                    )

        self.assertEqual(subevent.attendees.count(), 1)

        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.attendee_user.email]
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.event.refresh_from_db()
        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(subevent.attendees.count(), 0)

    def test_delete_attendees_from_event(self):
        subevent = mixer.blend(Event,
                               parent=self.event
                               )

        attendee = mixer.blend(User)

        EventAttendee.objects.create(
            event=subevent,
            user=None,
            name=attendee.name,
            email=attendee.email,
        )

        self.assertEqual(subevent.attendees.count(), 1)

        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.attendee_user.email]
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.event.refresh_from_db()
        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(subevent.attendees.count(), 1)
