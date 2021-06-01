from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.utils import translation
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from core.lib import get_language_options
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class EditNotificationsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()


    def tearDown(self):
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()

    def test_edit_notifications_by_owner(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        language
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "newsletter": True,
                "language": "en"
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editNotifications"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editNotifications"]["user"]["getsNewsletter"], True)
        self.assertEqual(data["editNotifications"]["user"]["emailNotifications"], True)
        self.assertEqual(data["editNotifications"]["user"]["language"], "en")


    def test_edit_notifications_by_admin(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        language
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "newsletter": False,
                "language": "en"
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editNotifications"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editNotifications"]["user"]["getsNewsletter"], False)
        self.assertEqual(data["editNotifications"]["user"]["emailNotifications"], True)
        self.assertEqual(data["editNotifications"]["user"]["language"], "en")


    def test_edit_notifications_by_logged_in_user(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "newsletter": False
                }
            }


        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_edit_notifications_by_anonymous(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "newsletter": False
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
