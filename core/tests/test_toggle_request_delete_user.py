from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class ToggleRequestDeleteUserTestCase(FastTenantTestCase):

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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["toggleRequestDeleteUser"]["viewer"]["guid"], self.user1.guid)

    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.send_mail_multi.delay')
    def test_call_send_email(self, mocked_send_mail_multi):
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

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        user_url = 'https://tenant.fast-test.com' + self.user1.url
        mocked_send_mail_multi.assert_called_once_with("fast_test", "Verzoek om account te verwijderen", 'email/toggle_request_delete_user_requested.html',
                                                       {'user_name': self.user1.name, 'user_url': user_url, 'site_url': 'https://tenant.fast-test.com', 'site_name': 'Pleio 2.0',
                                                        'primary_color': '#0e2f56', 'header_color': '#0e2f56'}, self.user1.email)

        result2 = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        mocked_send_mail_multi.assert_called_with("fast_test", "Verzoek om account te verwijderen geannuleerd", 'email/toggle_request_delete_user_cancelled.html',
                                                  {'user_name': self.user1.name, 'user_url': user_url, 'site_url': 'https://tenant.fast-test.com', 'site_name': 'Pleio 2.0',
                                                   'primary_color': '#0e2f56', 'header_color': '#0e2f56'}, self.user1.email)
