from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page, Row

class EditRowTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.user2 = mixer.blend(User)
        self.page = mixer.blend(Page,
                                owner=self.user,
                                read_access=[ACCESS_TYPE.public],
                                write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                )
        self.row1 = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.row2 = mixer.blend(Row, position=1, parent_id=self.page.guid, page=self.page)
        self.row3 = mixer.blend(Row, position=2, parent_id=self.page.guid, page=self.page)
        self.row4 = mixer.blend(Row, position=3, parent_id=self.page.guid, page=self.page)
        self.row5 = mixer.blend(Row, position=4, parent_id=self.page.guid, page=self.page)

    def test_edit_row_move_up_positions_by_admin(self):

        mutation = """
            mutation EditRow($input: editRowInput!) {
                editRow(input: $input) {
                    row {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.row2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editRow"]["row"]["position"], 3)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row3.id).position, 1)
        self.assertEqual(Row.objects.get(id=self.row4.id).position, 2)
        self.assertEqual(Row.objects.get(id=self.row5.id).position, 4)

    def test_edit_row_move_down_positions_by_admin(self):

        mutation = """
            mutation EditRow($input: editRowInput!) {
                editRow(input: $input) {
                    row {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.row4.guid,
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editRow"]["row"]["position"], 1)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row2.id).position, 2)
        self.assertEqual(Row.objects.get(id=self.row3.id).position, 3)
        self.assertEqual(Row.objects.get(id=self.row5.id).position, 4)


    def test_edit_row_move_up_positions_by_anonymous(self):

        mutation = """
            mutation EditRow($input: editRowInput!) {
                editRow(input: $input) {
                    row {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.row2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_edit_row_move_up_positions_by_user(self):

        mutation = """
            mutation EditRow($input: editRowInput!) {
                editRow(input: $input) {
                    row {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.row2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
