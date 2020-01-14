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
from cms.models import Page, Row

class AddRowTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, is_admin=True)
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row1 = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.row2 = mixer.blend(Row, position=1, parent_id=self.page.guid, page=self.page)

    def test_add_row_to_page_by_admin(self):

        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["addRow"]["row"]["position"], 1)
        self.assertEqual(data["addRow"]["row"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["parentGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["canEdit"], True)
        self.assertEqual(data["addRow"]["row"]["isFullWidth"], False)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row2.id).position, 2)


    def test_add_row_to_page_by_anonymous(self):

        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_add_row_to_page_by_user(self):

        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
