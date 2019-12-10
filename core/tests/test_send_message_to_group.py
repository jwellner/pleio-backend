from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class SendMessageToGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'member')
        self.group1.join(self.user3, 'member')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_to_group_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["sendMessageToGroup"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with("testMessageSubject", "email/send_message_to_group.html",
                                                       {"message": "<p>testMessageContent</p>"}, [self.user2.email, self.user3.email])

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_to_group_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["sendMessageToGroup"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with("testMessageSubject", "email/send_message_to_group.html",
                                                       {"message": "<p>testMessageContent</p>"}, [self.user2.email, self.user3.email])

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_to_group_by_group_member(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_to_group_by_other_user(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user4

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
        assert not mocked_send_mail_multi.called


    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_to_group_by_anonymous(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user3.guid]
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
        assert not mocked_send_mail_multi.called


    @mock.patch('core.resolvers.mutation_send_message_to_group.send_mail_multi')
    def test_send_message_as_test_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation SendMessageModal($input: sendMessageToGroupInput!) {
                sendMessageToGroup(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.group1.guid,
                "subject": "testMessageSubject",
                "message": "<p>testMessageContent</p>",
                "recipients": [self.user2.guid, self.user3.guid],
                "isTest": True
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["sendMessageToGroup"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with("testMessageSubject", "email/send_message_to_group.html",
                                                       {"message": "<p>testMessageContent</p>"}, [self.user1.email])
