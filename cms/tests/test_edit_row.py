from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page, Row


class EditRowTestCase(PleioTenantTestCase):

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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editRow"]["row"]["position"], 1)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row2.id).position, 2)
        self.assertEqual(Row.objects.get(id=self.row3.id).position, 3)
        self.assertEqual(Row.objects.get(id=self.row5.id).position, 4)

    def test_edit_row_move_up_positions_by_editor(self):
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

        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editRow"]["row"]["position"], 3)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row3.id).position, 1)
        self.assertEqual(Row.objects.get(id=self.row4.id).position, 2)
        self.assertEqual(Row.objects.get(id=self.row5.id).position, 4)

    def test_edit_row_move_down_positions_by_editor(self):
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

        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)
