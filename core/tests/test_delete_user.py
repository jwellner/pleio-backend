from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from unittest import mock


class DeleteUserTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()
        self.admin2 = AdminFactory()
        self.superadmin1 = UserFactory(is_superadmin=True)
        self.superadmin2 = UserFactory(is_superadmin=True)

        self.mutation = """
            mutation deleteUser($input: deleteUserInput!) {
                deleteUser(input: $input) {
                    success
                }
            }
        """
        self.variables = {"input": {"guid": self.user.guid}}

    def tearDown(self):
        super().tearDown()

    @mock.patch('core.resolvers.mutation_delete_user.schedule_user_delete_complete_mail')
    def test_delete_admin_by_admin(self, mocked_mail):
        self.variables['input']['guid'] = self.admin2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        data = result["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        self.assertEqual(mocked_mail.call_count, 2)

    @mock.patch('core.resolvers.mutation_delete_user.schedule_user_delete_complete_mail')
    def test_delete_user_by_admin(self, mocked_mail):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        data = result["data"]

        self.assertEqual(data["deleteUser"]["success"], True)
        self.assertEqual(mocked_mail.call_count, 1)

    def test_delete_user_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_delete_user_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_delete_superuser(self):
        self.variables['input']['guid'] = self.superadmin1.guid
        with self.assertGraphQlError("user_not_superadmin"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, self.variables)

    def test_delete_superuser_as_superuser(self):
        self.variables['input']['guid'] = self.superadmin1.guid

        self.graphql_client.force_login(self.superadmin2)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertTrue(result['data']['deleteUser']['success'])

