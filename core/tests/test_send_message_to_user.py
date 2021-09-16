from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class SendMessageToUserTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user1.profile.language = 'en'
        self.user1.profile.save()
        cache.set("%s%s" % (connection.schema_name, 'EXTRA_LANGUAGES'), ['en'])


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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_find")

    @mock.patch('core.resolvers.mutation_send_message_to_user.send_mail_multi.delay')
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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_send_message_to_user.send_mail_multi.delay')
    def test_call_send_email_with_copy_to_self(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        assert mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_send_message_to_user.send_mail_multi.delay')
    def test_call_not_send_email_with_copy_to_self(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        mocked_send_mail_multi.assert_called_once()