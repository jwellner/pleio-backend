from django.conf import settings
from django.db import connection
from django.test import TestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class SendMessageToUserTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

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

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

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

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_find")

    @mock.patch('core.resolvers.mutation_send_message_to_user.send_mail_multi')
    def test_call_send_email(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        mocked_send_mail_multi.assert_called_once_with('testMessageSubject', 'email/send_message_to_user.html', {'message': '<p>testMessageContent</p>'}, [self.user2.email],
                                                       [self.user1.email])
