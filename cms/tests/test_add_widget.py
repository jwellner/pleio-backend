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
from cms.models import Page, Row, Column

class AddWidgetTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, is_admin=True)
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.column1 = mixer.blend(Row, position=1, parent_id=self.row.guid, page=self.page, width=[6])

    def test_add_widget_to_column_by_admin(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["addWidget"]["widget"]["position"], 1)
        self.assertEqual(data["addWidget"]["widget"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addWidget"]["widget"]["parentGuid"], self.column1.guid)
        self.assertEqual(data["addWidget"]["widget"]["canEdit"], True)


    def test_add_widget_to_column_by_anonymous(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_add_widget_to_column_by_user(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
