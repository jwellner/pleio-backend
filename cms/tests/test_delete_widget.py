from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Widget
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page, Row, Column

class DeleteWidgetTestCase(FastTenantTestCase):

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
        self.row = mixer.blend(Row, position=0, page=self.page)
        self.column = mixer.blend(Column, position=0, row=self.row, page=self.page, width=[6])
        self.widget1 = mixer.blend(Widget, position=0, column=self.column, page=self.page)
        self.widget2 = mixer.blend(Widget, position=1, column=self.column, page=self.page)
        self.widget3 = mixer.blend(Widget, position=2, column=self.column, page=self.page)
        self.widget4 = mixer.blend(Widget, position=3, column=self.column, page=self.page)
        self.widget5 = mixer.blend(Widget, position=4, column=self.column, page=self.page)

    def test_delete_widget_by_admin(self):

        mutation = """
            mutation deleteWidget($input: deleteWidgetInput!) {
                deleteWidget(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget3.guid
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["deleteWidget"]["success"], True)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0)
        self.assertEqual(Widget.objects.get(id=self.widget2.id).position, 1)
        self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 2)
        self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 3)


    def test_delete_widget_by_user(self):

        mutation = """
            mutation deleteWidget($input: deleteWidgetInput!) {
                deleteWidget(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget3.guid
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_delete_widget_by_anonymous(self):

        mutation = """
            mutation deleteWidget($input: deleteWidgetInput!) {
                deleteWidget(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget3.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_delete_widget_by_other_user(self):

        mutation = """
            mutation deleteWidget($input: deleteWidgetInput!) {
                deleteWidget(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget3.guid
            }
        }

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
