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
from notifications.signals import notify


class MarkAllAsReadTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

    def test_mark_all_as_read_user_anon(self):
        mutation = """
            mutation NotificationsTop($input: markAllAsReadInput!) {
                markAllAsRead(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {}
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_mark_all_as_read(self):
        mutation = """
            mutation NotificationsTop($input: markAllAsReadInput!) {
                markAllAsRead(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {}
        }
        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["markAllAsRead"]["success"], True)
