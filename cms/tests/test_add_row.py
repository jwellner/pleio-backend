from core.constances import USER_ROLES
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from cms.models import Page, Row


class AddRowTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row1 = mixer.blend(Row, position=0, parent_id=self.page.guid, page=self.page)
        self.row2 = mixer.blend(Row, position=1, parent_id=self.page.guid, page=self.page)
        self.mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """

    def test_add_row_to_page_by_admin(self):
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["addRow"]["row"]["position"], 1)
        self.assertEqual(data["addRow"]["row"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["parentGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["canEdit"], True)
        self.assertEqual(data["addRow"]["row"]["isFullWidth"], False)
        self.assertEqual(Row.objects.get(id=self.row1.id).position, 0)
        self.assertEqual(Row.objects.get(id=self.row2.id).position, 2)

    def test_add_row_to_page_by_editor(self):
        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 0
            }
        }

        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["addRow"]["row"]["position"], 0)
        self.assertEqual(data["addRow"]["row"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["parentGuid"], self.page.guid)
        self.assertEqual(data["addRow"]["row"]["canEdit"], True)
        self.assertEqual(data["addRow"]["row"]["isFullWidth"], False)

        self.assertEqual(Row.objects.get(id=self.row1.id).position, 1)
        self.assertEqual(Row.objects.get(id=self.row2.id).position, 2)

    def test_add_row_to_page_by_anonymous(self):
        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_add_row_to_page_by_user(self):
        mutation = """
            mutation AddRow($rowInput: addRowInput!) {
                addRow(input: $rowInput) {
                    row {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        isFullWidth
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "rowInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.page.guid,
                "isFullWidth": False,
                "position": 1
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
