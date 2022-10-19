from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class ToggleUserIsBannedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.admin2 = mixer.blend(User, roles=['ADMIN'])

        self.mutation = """
            mutation toggleUserIsBanned($input: toggleUserIsBannedInput!) {
                toggleUserIsBanned(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()
        self.admin2.delete()
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

        with self.assertGraphQlError("could_not_save"):
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

        data = result["data"]
        self.assertEqual(data["toggleUserIsBanned"]["success"], True)

        result = self.graphql_client.post(self.mutation, variables)
        data = result["data"]
        self.assertEqual(data["toggleUserIsBanned"]["success"], True)

    def test_toggle_ban_yourself(self):
        variables = {
            "input": {
                "guid": self.admin.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)
