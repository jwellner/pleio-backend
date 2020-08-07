from django.conf import settings
from django.db import connection
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


class EditGroupNotificationsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group1 = mixer.blend(Group)
        self.group1.join(self.user1)
        self.group1.join(self.user2)


    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()

    def test_edit_group_notifications_by_owner(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": True,
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["editGroupNotifications"]["group"]["getsNotifications"], True)


    def test_edit_group_notifications_by_admin(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": True,
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
                }
            }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": False,
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["editGroupNotifications"]["group"]["getsNotifications"], False)

    def test_edit_group_notifications_by_logged_in_user(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": True,
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
                }
            }


        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_edit_group_notifications_by_owner_without_id(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": True,
                "guid": self.group1.guid
                }
            }


        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["editGroupNotifications"]["group"]["getsNotifications"], True)

    def test_edit_group_notifications_by_anonymous(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        getsNotifications
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "getsNotifications": True,
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
