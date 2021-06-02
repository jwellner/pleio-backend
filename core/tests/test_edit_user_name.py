from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from user.models import User
from django.core.cache import cache

class EditUserNameTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.user_other = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        cache.set("%s%s" % (connection.schema_name, 'EDIT_USER_NAME_ENABLED'), True)

    def tearDown(self):
        self.user.delete()
        self.user_other.delete()
        self.admin.delete()

    def test_edit_user_name_by_admin(self):

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editUserName"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editUserName"]["user"]["name"], "Jantje")


    def test_edit_user_name_by_anonymous(self):

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_edit_user_name_by_self(self):

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editUserName"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editUserName"]["user"]["name"], "Jantje")

    def test_edit_user_name_by_self_disabled(self):
        cache.set("%s%s" % (connection.schema_name, 'EDIT_USER_NAME_ENABLED'), False)

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_edit_user_name_by_other_user(self):

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        request = HttpRequest()
        request.user = self.user_other

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")