from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Widget
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class EditGroupWidgetTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group = mixer.blend(Group, owner=self.user1)
        self.widget = Widget.objects.create(group=self.group, position=0,
                                            settings=[{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}])

    def tearDown(self):
        self.group.delete()
        self.admin.delete()
        self.user1.delete()


    def test_edit_group_widget(self):
        mutation = """
            mutation editGroupWidget($input: editGroupWidgetInput!) {
                editGroupWidget(input: $input) {
                    entity {
                    guid
                    ... on Widget {
                        containerGuid
                        parentGuid
                        settings {
                            key
                            value
                            __typename
                        }
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
            
        """
        variables = {
            "input": {
                "guid": self.widget.guid,
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key5", "value": "value5"}, {"key": "key3", "value": "value3"}]
            }
        }

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertIsNotNone(data["editGroupWidget"]["entity"]["guid"])
        self.assertEqual(data["editGroupWidget"]["entity"]["containerGuid"], self.group.guid)
        self.assertEqual(data["editGroupWidget"]["entity"]["parentGuid"], self.group.guid)
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][0]["key"], "key1")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][0]["value"], "value1")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][1]["key"], "key5")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][1]["value"], "value5")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][2]["key"], "key3")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][2]["value"], "value3")
