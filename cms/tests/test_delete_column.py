from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page, Row, Column

class DeleteColumnTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.user2 = mixer.blend(User)
        self.page = mixer.blend(Page,
                                owner=self.user,
                                read_access=[ACCESS_TYPE.public],
                                write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                )
        self.row = mixer.blend(Row, position=0, page=self.page)
        self.column1 = mixer.blend(Column, position=0, row=self.row, page=self.page, width=[3])
        self.column2 = mixer.blend(Column, position=1, row=self.row, page=self.page, width=[3])
        self.column3 = mixer.blend(Column, position=2, row=self.row, page=self.page, width=[3])
        self.column4 = mixer.blend(Column, position=3, row=self.row, page=self.page, width=[3])
        self.column5 = mixer.blend(Column, position=4, row=self.row, page=self.page, width=[3])

    def test_delete_column_by_admin(self):

        mutation = """
            mutation deleteColumn($input: deleteColumnInput!) {
                deleteColumn(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.column3.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteColumn"]["success"], True)
        self.assertEqual(Column.objects.get(id=self.column1.id).position, 0)
        self.assertEqual(Column.objects.get(id=self.column2.id).position, 1)
        self.assertEqual(Column.objects.get(id=self.column4.id).position, 2)
        self.assertEqual(Column.objects.get(id=self.column5.id).position, 3)

    def test_delete_column_by_editor(self):

        mutation = """
            mutation deleteColumn($input: deleteColumnInput!) {
                deleteColumn(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.column3.guid
            }
        }

        request = HttpRequest()
        request.user = self.editor

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteColumn"]["success"], True)
        self.assertEqual(Column.objects.get(id=self.column1.id).position, 0)
        self.assertEqual(Column.objects.get(id=self.column2.id).position, 1)
        self.assertEqual(Column.objects.get(id=self.column4.id).position, 2)
        self.assertEqual(Column.objects.get(id=self.column5.id).position, 3)

    def test_delete_column_by_user(self):

        mutation = """
            mutation deleteColumn($input: deleteColumnInput!) {
                deleteColumn(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.column3.guid
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_delete_column_by_anonymous(self):

        mutation = """
            mutation deleteColumn($input: deleteColumnInput!) {
                deleteColumn(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.column3.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_delete_column_by_other_user(self):

        mutation = """
            mutation deleteColumn($input: deleteColumnInput!) {
                deleteColumn(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.column3.guid
            }
        }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
