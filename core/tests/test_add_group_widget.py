from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError

class AddGroupWidgetTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group = mixer.blend(Group, owner=self.user1)

    def tearDown(self):
        self.group.delete()
        self.admin.delete()
        self.user1.delete()


    def test_add_group_widget(self):
        mutation = """
            mutation AddGroupWidget($input: addGroupWidgetInput!) {
                addGroupWidget(input: $input) {
                    entity {
                        guid
                        containerGuid
                        parentGuid
                        type
                        settings {
                            key
                            value
                        }
                        __typename
                        }
                        __typename
                }
            }
        """
        variables = {
            "input": {
                "groupGuid": self.group.guid,
                "position": 0,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}]
            }
        }

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertIsNotNone(data["addGroupWidget"]["entity"]["guid"])
        self.assertEqual(data["addGroupWidget"]["entity"]["containerGuid"], self.group.guid)
        self.assertEqual(data["addGroupWidget"]["entity"]["parentGuid"], self.group.guid)
        self.assertEqual(data["addGroupWidget"]["entity"]["type"], "linklist")
        self.assertEqual(data["addGroupWidget"]["entity"]["settings"][0]["key"], "key1")
