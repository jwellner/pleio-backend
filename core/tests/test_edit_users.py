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


class EditUsersTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User, is_active=False)
        self.user6 = mixer.blend(User, is_active=False)
        self.admin = mixer.blend(User, roles=['ADMIN'])

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()

    def test_edit_users_by_anonymous(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user1.guid],
                "action": "ban"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_edit_users_by_user(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid],
                "action": "ban"
            }
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_ban_users_by_admin(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid, self.user3.guid],
                "action": "ban"
            }
        }

        request = HttpRequest()
        request.user = self.admin

        self.assertEqual(User.objects.filter(is_active=False).count(), 2) 

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]
        self.assertEqual(data["editUsers"]["success"], True)

        self.assertEqual(User.objects.filter(is_active=False).count(), 4)        

    def test_unban_users_by_admin(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user5.guid],
                "action": "unban"
            }
        }

        request = HttpRequest()
        request.user = self.admin

        self.assertEqual(User.objects.filter(is_active=False).count(), 2) 

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]
        self.assertEqual(data["editUsers"]["success"], True)

        self.assertEqual(User.objects.filter(is_active=False).count(), 1)   


    def test_ban_yourself(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid, self.admin.guid],
                "action": "ban"
            }
        }
        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
