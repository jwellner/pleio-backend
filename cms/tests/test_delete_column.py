from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page, Row, Column


class DeleteColumnTestCase(PleioTenantTestCase):

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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        self.graphql_client.force_login(self.editor)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)
