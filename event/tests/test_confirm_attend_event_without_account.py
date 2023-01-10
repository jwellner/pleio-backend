from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from user.factories import UserFactory
from event.models import Event, EventAttendee, EventAttendeeRequest
from mixer.backend.django import mixer
from unittest import mock


class ConfirmAttendEventWithoutAccountTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.event = EventFactory(
            owner=UserFactory(),
            location="place",
            location_link="test.com",
            location_address="Straat 10",
            max_attendees=1,
            attend_event_without_account=True,
            attendee_welcome_mail_content=self.tiptap_paragraph("Welcome!")
        )

        EventAttendeeRequest.objects.create(code='1234567890', email='pete@tenant.fast-test.com', event=self.event)
        EventAttendeeRequest.objects.create(code='1234567890', email='test@tenant.fast-test.com', event=self.event)

        self.mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        attendees {
                            total
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

    @mock.patch("event.mail_builders.attendee_welcome_mail.send_mail")
    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.submit_attend_event_wa_confirm')
    def test_confirm_attend_event_without_account(self, mocked_send_mail, mocked_welcome_mail):
        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "pete@tenant.fast-test.com"
            }
        }

        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["attendees"]["edges"], [])
        self.assertEqual(1, mocked_send_mail.call_count)
        self.assertEqual(mocked_welcome_mail.call_args.kwargs, {
            'attendee': self.event.attendees.get(email=variables['input']['email'])
        })

    def test_confirm_attend_event_is_full_without_account(self):
        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "pete@tenant.fast-test.com"
            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticated_user,
            email=self.authenticated_user.email
        )

        with self.assertGraphQlError("event_is_full"):
            self.graphql_client.post(self.mutation, variables)

    def test_confirm_delete_attend_event_without_account(self):
        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "test@tenant.fast-test.com",
                "delete": True
            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=None,
            email='test@tenant.fast-test.com'
        )

        self.assertEqual(self.event.attendees.exclude(user__isnull=False).count(), 1)

        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["attendees"]["edges"], [])
        self.assertEqual(self.event.attendees.exclude(user__isnull=False).count(), 0)

    def test_confirm_attend_event_is_full_without_account_waitinglist(self):
        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "state": "waitinglist",
                "email": "pete@tenant.fast-test.com"

            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticated_user,
            email=self.authenticated_user.email,
        )

        self.graphql_client.post(self.mutation, variables)
        self.assertEqual(self.event.attendees.filter(state='waitinglist').count(), 1)

    def test_confirm_attend_event_without_account_already_registered(self):
        EventAttendeeRequest.objects.create(code='1234567890', email='registered@tenant.fast-test.com', event=self.event)
        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            email='registered@tenant.fast-test.com'
        )

        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "registered@tenant.fast-test.com",
                "state": "accept"
            }
        }

        with self.assertGraphQlError('email_already_used'):
            self.graphql_client.post(self.mutation, variables)
