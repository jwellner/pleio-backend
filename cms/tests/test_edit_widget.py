from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User, Widget
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page, Row, Column

class EditWidgetTestCase(FastTenantTestCase):

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
        self.row = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.column = mixer.blend(Column, position=0, parent_id=self.row.guid, page=self.page, width=[6])
        self.widget1 = mixer.blend(Widget, position=0, parent_id=self.column.guid, page=self.page)
        self.widget2 = mixer.blend(Widget, position=1, parent_id=self.column.guid, page=self.page)
        self.widget3 = mixer.blend(Widget, position=2, parent_id=self.column.guid, page=self.page)
        self.widget4 = mixer.blend(Widget, position=3, parent_id=self.column.guid, page=self.page)
        self.widget5 = mixer.blend(Widget, position=4, parent_id=self.column.guid, page=self.page)

    def test_edit_widget_move_up_positions_by_admin(self):

        mutation = """
            mutation EditWidget($input: editWidgetInput!) {
                editWidget(input: $input) {
                    widget {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editWidget"]["widget"]["position"], 3)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0)
        self.assertEqual(Widget.objects.get(id=self.widget3.id).position, 1)
        self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 2)
        self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 4)

    def test_edit_widget_move_down_positions_by_admin(self):

        mutation = """
            mutation EditWidget($input: editWidgetInput!) {
                editWidget(input: $input) {
                    widget {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget4.guid,
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editWidget"]["widget"]["position"], 1)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0)
        self.assertEqual(Widget.objects.get(id=self.widget2.id).position, 2)
        self.assertEqual(Widget.objects.get(id=self.widget3.id).position, 3)
        self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 4)


    def test_edit_widget_move_up_positions_by_anonymous(self):

        mutation = """
            mutation EditWidget($input: editWidgetInput!) {
                editWidget(input: $input) {
                    widget {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_edit_widget_move_up_positions_by_user(self):

        mutation = """
            mutation EditWidget($input: editWidgetInput!) {
                editWidget(input: $input) {
                    widget {
                        guid
                        position
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.widget2.guid,
                "position": 3
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
