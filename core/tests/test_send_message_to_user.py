from django.db import connection
from django.core.cache import cache
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class SendMessageToUserTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user1.profile.language = 'en'
        self.user1.profile.save()
        cache.set("%s%s" % (connection.schema_name, 'EXTRA_LANGUAGES'), ['en'])

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

        super().tearDown()

    def test_send_message_to_user_anon(self):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user2.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_send_message_to_user(self):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user2.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result['data']

        self.assertEqual(data["sendMessageToUser"]["success"], True)

    def test_send_message_to_unknown_user_guid(self):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": "11111111-1111-1111-1111-111111111111",
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>"
            }
        }

        with self.assertGraphQlError("could_not_find"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    @mock.patch('core.resolvers.mutation_send_message_to_user.schedule_user_send_message_mail')
    def test_call_send_email(self, mocked_mail):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user2.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>"
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(mutation, variables)

        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_send_message_to_user.schedule_user_send_message_mail')
    def test_call_send_email_with_copy_to_self(self, mocked_mail):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user2.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": True
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(mutation, variables)

        self.assertTrue(mocked_mail.called)

    @mock.patch('core.resolvers.mutation_send_message_to_user.schedule_user_send_message_mail')
    def test_call_not_send_email_with_copy_to_self(self, mocked_mail):
        mutation = """
            mutation SendMessageModal($input: sendMessageToUserInput!) {
                sendMessageToUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user2.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "sendCopyToSender": False
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(mutation, variables)

        self.assertEqual(mocked_mail.call_count, 1)
