from django.utils import timezone
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from user.factories import UserFactory, AdminFactory
from event.models import EventAttendee
from unittest import mock

class EditEventAttendeeTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.today = timezone.now()
        self.attendee_user = UserFactory()
        self.owner = UserFactory()
        self.admin = AdminFactory()
        self.event = EventFactory(self.owner,
                                  attend_event_without_account=True)

        self.attendee1 = EventAttendee.objects.create(
            event=self.event,
            user=self.attendee_user,
            email=self.attendee_user.email,
            checked_in_at=self.today
        )
        self.attendee2 = EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test1@test.nl",
            
        )
        self.attendee3 = EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test2@test.nl"
        )

        self.mutation = """
            mutation editEventAttendee($input: editEventAttendeeInput!) {
                editEventAttendee(input: $input) {
                    entity {
                        guid
                        attendees {
                            edges {
                                email
                                timeCheckedIn
                            }
                        }
                    }
                    __typename
                }
            }
        """

    def test_edit_attendee_from_event_by_admin(self):
        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddress": "test2@test.nl",
                "timeCheckedIn": self.today.isoformat()
            }
        }

        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(self.mutation, variables)

        self.attendee3.refresh_from_db()
        self.assertEqual(self.attendee3.checked_in_at, self.today)
        self.assertEqual(self.attendee3.email, "test2@test.nl")
        self.assertEqual(self.attendee3.event, self.event)

    @mock.patch('event.mail_builders.attend_event_confirm.submit_attend_event_wa_confirm')
    def test_edit_attendee_by_event_owner(self, mocked_send_mail):
        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddress": self.attendee_user.email,
                "timeCheckedIn": None
            }
        }

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.mutation, variables)

        self.attendee1.refresh_from_db()
        self.assertEqual(self.attendee1.checked_in_at, None)
        self.assertEqual(self.attendee1.user.email, self.attendee_user.email)
        self.assertEqual(self.attendee1.event, self.event)

    @mock.patch('event.mail_builders.attend_event_confirm.submit_attend_event_wa_confirm')
    def test_edit_attendee_by_user(self, mocked_send_mail):
        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddress": self.attendee_user.email,
                "timeCheckedIn": None
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.attendee_user)
            self.graphql_client.post(self.mutation, variables)
