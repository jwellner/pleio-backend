from core.models import Widget
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page, Row, Column


class DeleteWidgetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteWidget"]["success"], True)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0)
        self.assertEqual(Widget.objects.get(id=self.widget2.id).position, 1)
        self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 2)
        self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 3)

    def test_delete_widget_by_editor(self):
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

        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)
