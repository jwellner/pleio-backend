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


class ToggleRequestDeleteUserTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)

    def tearDown(self):
        self.user1.delete()

    def test_send_message_to_user_anon(self):
        mutation = """
            mutation toggleRequestDeleteUser($input: toggleRequestDeleteUserInput!) {
                toggleRequestDeleteUser(input: $input) {
                    viewer {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_toggle_request_delete_user(self):
        mutation = """
            mutation toggleRequestDeleteUser($input: toggleRequestDeleteUserInput!) {
                toggleRequestDeleteUser(input: $input) {
                    viewer {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["toggleRequestDeleteUser"]["viewer"], None)

    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.EmailMessage')
    def test_call_send_email(self, mocked_EmailMessage):
        mutation = """
            mutation toggleRequestDeleteUser($input: toggleRequestDeleteUserInput!) {
                toggleRequestDeleteUser(input: $input) {
                    viewer {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        mocked_EmailMessage.assert_called_once_with("Request to remove account", f"You, as user, <strong> {self.user1.name} </strong> have requested that your account be removed. You will be informed once the website             administrator has done so.", settings.FROM_EMAIL, [self.user1.email])

        result2 = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        mocked_EmailMessage.assert_called_with("Request to remove account cancelled", f"You, as <strong> {self.user1.name} </strong> user, have cancelled your request to remove your account.", settings.FROM_EMAIL, [self.user1.email])
