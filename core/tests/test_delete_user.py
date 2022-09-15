from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from unittest import mock


class DeleteUserTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()
        self.admin2 = AdminFactory()

        self.mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        self.variables = {"input": {"guid": self.user.guid}}

    def tearDown(self):
        self.user.delete()
        self.admin.delete()
        self.admin2.delete()
        super().tearDown()

    @mock.patch('core.resolvers.mutation_delete_user.schedule_user_delete_complete_mail')
    def test_delete_admin_by_admin(self, mocked_send_mail_multi):
        self.variables['input']['guid'] = self.admin2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        data = result["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('core.resolvers.mutation_delete_user.schedule_user_delete_complete_mail')
    def test_delete_user_by_admin(self, mocked_send_mail_multi):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        data = result["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        mocked_send_mail_multi.assert_called_once()

    def test_delete_user_by_user(self):
        with self.assertGraphQlError("could_not_delete"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_delete_user_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)
