from unittest import mock
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from event.models import Event, EventAttendeeRequest
from user.models import User


class AttendEventTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(
            Event,
            qr_access=True,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            attend_event_without_account=True
        )
        EventAttendeeRequest.objects.create(code='1234567890', email='pete@tenant.fast-test.com', event=self.event)

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    @mock.patch("event.resolvers.mutation_attend_event.submit_mail_event_qr")
    def test_attend_event_with_qr_access(self, mocked_send_mail):
        mutation = """
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

        variables = {
            "input": {
                "guid": self.event.guid,
                "state": 'accept'
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result['data']['attendEvent']['entity']
        self.assertEqual(entity['attendees']['edges'][0]['name'], self.authenticatedUser.name)
        self.assertTrue(mocked_send_mail.called)

    @mock.patch("event.resolvers.mutation_confirm_attend_event_without_account.submit_mail_event_qr")
    @mock.patch("event.resolvers.mutation_confirm_attend_event_without_account.submit_attend_event_wa_confirm")
    def test_attend_event_with_qr_access_without_account(self, mocked_send_confirm_mail, mocked_send_qr_mail):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                attendEventWA: confirmAttendEventWithoutAccount(input: $input) {
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

        variables = {
            "input": {
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "pete@tenant.fast-test.com"
            }
        }

        result = self.graphql_client.post(mutation, variables)
        entity = result['data']['attendEventWA']['entity']
        self.assertEqual(entity['attendees']['total'], 1)
        self.assertEqual(entity['attendees']['edges'], [])
        self.assertTrue(mocked_send_qr_mail.called)
        self.assertTrue(mocked_send_confirm_mail.called)
