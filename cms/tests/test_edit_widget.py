from core.models import Widget
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page, Row, Column


class EditWidgetTestCase(PleioTenantTestCase):

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
        self.other_column = mixer.blend(Column, position=0, row=self.row, page=self.page, width=[6])
        self.widget1 = mixer.blend(Widget, position=0, column=self.column, page=self.page)
        self.widget2 = mixer.blend(Widget, position=1, column=self.column, page=self.page)
        self.widget3 = mixer.blend(Widget, position=2, column=self.column, page=self.page)
        self.widget4 = mixer.blend(Widget, position=3, column=self.column, page=self.page)
        self.widget5 = mixer.blend(Widget, position=4, column=self.column, page=self.page)

        self.mutation = """
            mutation EditWidget($input: editWidgetInput!) {
                editWidget(input: $input) {
                    widget {
                        guid
                        position
                        parentGuid
                        settings {
                            key
                            value
                            richDescription
                        }
                    }
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.widget2.guid,
                "position": 3,
                "settings": [{
                    'key': 'tags',
                    'value': "['foo', 'bar']",
                    'richDescription': None,
                }]
            }
        }

    def test_edit_widget_move_up_positions_by_admin(self):
        for (user, message) in [(self.admin, "as admin"),
                                (self.editor, 'as editor')]:
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.variables)

            widget = result["data"]["editWidget"]["widget"]
            self.assertDictEqual(widget['settings'][0], self.variables['input']['settings'][0], msg=message)
            self.assertEqual(widget["position"], self.variables['input']['position'], msg=message)
            self.assertEqual(widget["guid"], self.variables['input']['guid'], msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget3.id).position, 1, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 2, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 4, msg=message)

    def test_edit_widget_move_down_positions(self):
        variables = {
            "input": {
                "guid": self.widget4.guid,
                "position": 1
            }
        }

        for (user, message) in [(self.admin, "as admin"),
                                (self.editor, 'as editor')]:
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, variables)

            data = result["data"]
            self.assertEqual(data["editWidget"]["widget"]["position"], 1, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget2.id).position, 2, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget3.id).position, 3, msg=message)
            self.assertEqual(Widget.objects.get(id=self.widget5.id).position, 4, msg=message)

    def test_edit_widget_move_up_positions_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_widget_move_up_positions_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_widget_that_doesnt_exists(self):
        self.widget2.delete()
        with self.assertGraphQlError("could_not_find"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_parent_that_doesnt_exist_of_widget(self):
        self.variables['input']['parentGuid'] = self.other_column.guid
        self.other_column.delete()

        with self.assertGraphQlError("could_not_find"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_parent_that_does_exist_of_widget(self):
        self.variables['input']['guid'] = self.widget1.guid
        self.variables['input']['parentGuid'] = self.other_column.guid

        for (user, message) in [(self.admin, "as admin"),
                                (self.editor, 'as editor')]:
            self.graphql_client.force_login(user)
            response = self.graphql_client.post(self.mutation, self.variables)
            widget = response['data']['editWidget']['widget']
            self.assertEqual(widget['guid'], self.widget1.guid, msg=message)
            self.assertEqual(widget['parentGuid'], self.other_column.guid, msg=message)
