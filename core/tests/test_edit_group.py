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

class EditGroupCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user)

    def test_edit_group_anon(self):

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        name
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "name": "test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_edit_group(self):

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        description
                        excerpt
                        richDescription
                        introduction
                        welcomeMessage
                        isClosed
                        isMembershipOnRequest
                        isFeatured
                        autoNotification
                        tags
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "name": "Name",
                "icon": "/icon.png",
                "description": "description",
                "richDescription": "<p>richDescription</p>",
                "introduction": "introdcution",
                "welcomeMessage": "welcomeMessage",
                "isClosed": True,
                "isMembershipOnRequest": True,
                "isFeatured": True,
                "autoNotification": True,
                "tags": ["tag_one", "tag_two"]
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editGroup"]["group"]["guid"], variables["group"]["guid"])
        self.assertEqual(data["editGroup"]["group"]["name"], variables["group"]["name"])
        self.assertEqual(data["editGroup"]["group"]["icon"], variables["group"]["icon"])
        self.assertEqual(data["editGroup"]["group"]["description"], variables["group"]["description"])
        self.assertEqual(data["editGroup"]["group"]["excerpt"], variables["group"]["description"])
        self.assertEqual(data["editGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["editGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["editGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["editGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["editGroup"]["group"]["isMembershipOnRequest"], variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["editGroup"]["group"]["isFeatured"], variables["group"]["isFeatured"])
        self.assertEqual(data["editGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["editGroup"]["group"]["tags"], ["tag_one", "tag_two"])
