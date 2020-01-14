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

class AddColumnTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, is_admin=True)
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row1 = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.row2 = mixer.blend(Row, position=1, parent_id=self.page.guid, page=self.page)

    def test_add_column_to_row_by_admin(self):

        mutation = """
            mutation AddColumn($columnInput: addColumnInput!) {
                addColumn(input: $columnInput) {
                    column {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        width
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "columnInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.row1.guid,
                "position": 1,
                "width": [6]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["addColumn"]["column"]["position"], 1)
        self.assertEqual(data["addColumn"]["column"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addColumn"]["column"]["parentGuid"], self.row1.guid)
        self.assertEqual(data["addColumn"]["column"]["canEdit"], True)
        self.assertEqual(data["addColumn"]["column"]["width"][0], 6)

    def test_add_column_to_row_by_anonymous(self):

        mutation = """
            mutation AddColumn($columnInput: addColumnInput!) {
                addColumn(input: $columnInput) {
                    column {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        width
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "columnInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.row1.guid,
                "position": 1,
                "width": [6]
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_add_column_to_row_by_user(self):

        mutation = """
            mutation AddColumn($columnInput: addColumnInput!) {
                addColumn(input: $columnInput) {
                    column {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        width
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "columnInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.row1.guid,
                "position": 1,
                "width": [6]
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
