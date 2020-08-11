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


class MarkAsReadTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

    def test_mark_as_read_user_anon(self):
        mutation = """
            mutation Notification($input: markAsReadInput!) {
                markAsRead(input: $input) {
                    success
                    notification {
                    id
                    isUnread
                    __typename
                    }
                    __typename
                }
            }

        """
        notificationid = 1
        variables = {
            "input": {
                "id": notificationid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        errors = result[1]["errors"]
        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_mark_as_read(self):
        mutation = """
            mutation Notification($input: markAsReadInput!) {
                markAsRead(input: $input) {
                    success
                    notification {
                    id
                    isUnread
                    __typename
                    }
                    __typename
                }
            }

        """
        request = HttpRequest()
        request.user = self.user1
        notification = notify.send(request.user, recipient=request.user, verb='welcome')[0][1][0]

        variables = {
            "input": {
                "id": notification.id
            }
        }
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["markAsRead"]["success"], True)
        self.assertEqual(data["markAsRead"]["notification"]["isUnread"], False)
        self.assertEqual(data["markAsRead"]["notification"]["id"], notification.id)
