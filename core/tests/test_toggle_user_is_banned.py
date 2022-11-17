from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class ToggleUserIsBannedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory()
        self.admin = AdminFactory()
        self.admin2 = AdminFactory()

        self.mutation = """
            mutation toggleRequestBanUser($input: toggleUserIsBannedInput!) {
                toggleUserIsBanned(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()
        super().tearDown()

    def test_toggle_is_banned_by_anonymous(self):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_is_banned_by_user(self):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_is_banned_by_admin(self):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)
        self.assertEqual(result["data"]["toggleUserIsBanned"]["success"], True)

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)
        self.assertEqual(result["data"]["toggleUserIsBanned"]["success"], True)

    def test_toggle_ban_yourself(self):
        variables = {
            "input": {
                "guid": self.admin.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_ban_for_superadmin(self):
        variables = {
            "input": {
                "guid": UserFactory(is_superadmin=True).guid
            }
        }

        with self.assertGraphQlError("user_not_superadmin"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_ban_for_superadmin_as_superadmin(self):
        variables = {
            "input": {
                "guid": UserFactory(is_superadmin=True).guid
            }
        }

        self.graphql_client.force_login(UserFactory(is_superadmin=True))
        result = self.graphql_client.post(self.mutation, variables)
        self.assertEqual(result["data"]["toggleUserIsBanned"]["success"], True)
