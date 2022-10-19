from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event, EventAttendee
from mixer.backend.django import mixer
from unittest import mock


class AttendEventWithoutAccountTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event)
        self.event.max_attendees = 1
        self.event.save()

        self.mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEvent: attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.event.guid,
                "name": "Pete",
                "email": "pete@tenant.fast-test.com"
            }
        }
        mock.patch('event.resolvers.mutation_attend_event.generate_code', return_value='6df8cdad5582833eeab4')

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_create_attend_event_without_account_request(self):
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_resend(self):
        self.graphql_client.post(self.mutation, self.variables)

        self.variables['input']['resend'] = True
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_attend_twice(self):
        # given
        self.graphql_client.post(self.mutation, self.variables)

        # when, then
        with self.assertGraphQlError("email_already_used"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_attend_event_is_full_without_account(self):
        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser,
            email=self.authenticatedUser.email
        )

        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_no_name(self):
        # Given
        self.variables['input']['name'] = ""

        # When, then
        with self.assertGraphQlError("invalid_name"):
            self.graphql_client.post(self.mutation, self.variables)
