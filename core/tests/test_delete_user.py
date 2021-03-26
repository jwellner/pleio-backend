from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from django.test import override_settings
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from user.models import User
from unittest import mock

class DeleteUserTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.admin2 = mixer.blend(User, roles=['ADMIN'])


    def tearDown(self):
        self.user.delete()
        self.admin.delete()
        self.admin2.delete()


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_delete_user.send_mail_multi.delay')
    def test_delete_admin_by_admin(self, mocked_send_mail_multi):

        mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.admin2.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        self.assertEqual(mocked_send_mail_multi.call_count, 2)


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_delete_user.send_mail_multi.delay')
    def test_delete_user_by_admin(self, mocked_send_mail_multi):

        mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        mocked_send_mail_multi.assert_called_once()


    def test_delete_user_by_user(self):

        mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_delete")


    def test_delete_user_by_anonymous(self):

        mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
