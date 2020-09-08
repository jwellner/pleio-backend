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


class ToggleUserIsBannedTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.admin2 = mixer.blend(User, is_admin=True)

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()

    def test_toggle_is_banned_by_anonymous(self):
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


    def test_toggle_is_banned_by_user(self):
        mutation = """
            mutation toggleUserIsBanned($input: toggleUserIsBannedInput!) {
                toggleUserIsBanned(input: $input) {
                    success
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

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_toggle_is_banned_by_admin(self):
        mutation = """
            mutation toggleUserIsBanned($input: toggleUserIsBannedInput!) {
                toggleUserIsBanned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]
        self.assertEqual(data["toggleUserIsBanned"]["success"], True)

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]
        self.assertEqual(data["toggleUserIsBanned"]["success"], True)



    def test_toggle_ban_yourself(self):
        mutation = """
            mutation toggleUserIsBanned($input: toggleUserIsBannedInput!) {
                toggleUserIsBanned(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.admin.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
