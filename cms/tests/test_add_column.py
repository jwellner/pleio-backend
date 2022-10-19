from core.constances import USER_ROLES
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from cms.models import Page, Row


class AddColumnTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row1 = mixer.blend(Row, position=0, page=self.page)
        self.row2 = mixer.blend(Row, position=1, page=self.page)
        self.mutation = """
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
        self.variables = {
            "columnInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.row1.guid,
                "position": 1,
                "width": [6]
            }
        }

    def test_add_column_to_row_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["addColumn"]["column"]["position"], 1)
        self.assertEqual(data["addColumn"]["column"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addColumn"]["column"]["parentGuid"], self.row1.guid)
        self.assertEqual(data["addColumn"]["column"]["canEdit"], True)
        self.assertEqual(data["addColumn"]["column"]["width"][0], 6)

    def test_add_column_to_row_by_editor(self):
        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["addColumn"]["column"]["position"], 1)
        self.assertEqual(data["addColumn"]["column"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addColumn"]["column"]["parentGuid"], self.row1.guid)
        self.assertEqual(data["addColumn"]["column"]["canEdit"], True)
        self.assertEqual(data["addColumn"]["column"]["width"][0], 6)

    def test_add_column_to_row_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_add_column_to_row_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)
