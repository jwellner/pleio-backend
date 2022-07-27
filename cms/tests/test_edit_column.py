from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page, Row, Column


class EditColumnTestCase(PleioTenantTestCase):

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
        self.other_row = mixer.blend(Row, position=1, page=self.page)

        self.column1 = mixer.blend(Column, position=0, row=self.row, page=self.page, width=[3])
        self.column2 = mixer.blend(Column, position=1, row=self.row, page=self.page, width=[3])
        self.column3 = mixer.blend(Column, position=2, row=self.row, page=self.page, width=[3])
        self.column4 = mixer.blend(Column, position=3, row=self.row, page=self.page, width=[3])
        self.column5 = mixer.blend(Column, position=4, row=self.row, page=self.page, width=[3])

        self.mutation = """
            mutation EditColumn($input: editColumnInput!) {
                editColumn(input: $input) {
                    column {
                        guid
                        parentGuid
                        position,
                        width
                    }
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.column2.guid,
                "position": 3,
                "width": [2],
            }
        }

    def test_edit_column_move_up_positions_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        column = result["data"]["editColumn"]["column"]
        self.assertEqual(column["position"], self.variables['input']['position'])
        self.assertEqual(column["width"], self.variables['input']['width'])

        self.assertEqual(Column.objects.get(id=self.column1.id).position, 0)
        self.assertEqual(Column.objects.get(id=self.column3.id).position, 1)
        self.assertEqual(Column.objects.get(id=self.column4.id).position, 2)
        self.assertEqual(Column.objects.get(id=self.column5.id).position, 4)

    def test_edit_column_move_up_positions_by_editor(self):
        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["editColumn"]["column"]["position"], 3)
        self.assertEqual(Column.objects.get(id=self.column1.id).position, 0)
        self.assertEqual(Column.objects.get(id=self.column3.id).position, 1)
        self.assertEqual(Column.objects.get(id=self.column4.id).position, 2)
        self.assertEqual(Column.objects.get(id=self.column5.id).position, 4)

    def test_edit_column_move_down_positions_by_admin(self):
        variables = {
            "input": {
                "guid": self.column4.guid,
                "position": 1
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["editColumn"]["column"]["position"], 1)
        self.assertEqual(Column.objects.get(id=self.column1.id).position, 0)
        self.assertEqual(Column.objects.get(id=self.column2.id).position, 2)
        self.assertEqual(Column.objects.get(id=self.column3.id).position, 3)
        self.assertEqual(Column.objects.get(id=self.column5.id).position, 4)

    def test_edit_column_move_up_positions_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_column_move_up_positions_by_user(self):
        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_column_that_does_not_exists(self):
        self.column2.delete()
        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, self.variables)

    def test_move_to_another_row(self):
        variables = {
            "input": {
                "guid": self.column4.guid,
                "parentGuid": self.other_row.guid,
            }
        }
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        column = result['data']['editColumn']['column']
        self.assertEqual(column['parentGuid'], self.other_row.guid)

    def test_move_to_nonexistent_row(self):
        variables = {
            "input": {
                "guid": self.column4.guid,
                "parentGuid": self.other_row.guid,
                "position": 1
            }
        }
        self.other_row.delete()

        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)
