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


class ToggleUserRoleTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.admin2 = mixer.blend(User, roles=['ADMIN'])

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()

    def test_toggle_request_delete_user_by_anonymous(self):
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


    def test_toggle_user_role_by_user(self):
        mutation = """
            mutation toggleUserRole($input: toggleUserRoleInput!) {
                toggleUserRole(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "role": "admin"
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_toggle_user_role.send_mail_multi.delay')
    def test_toggle_user_role_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation toggleUserRole($input: toggleUserRoleInput!) {
                toggleUserRole(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "role": "admin"
            }
        }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]
        self.assertEqual(data["toggleUserRole"]["success"], True)

        self.assertEqual(mocked_send_mail_multi.call_count, 3)

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]
        self.assertEqual(data["toggleUserRole"]["success"], True)

        self.assertEqual(mocked_send_mail_multi.call_count, 6)