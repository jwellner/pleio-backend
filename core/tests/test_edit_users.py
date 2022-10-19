from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditUsersTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User, is_active=False)
        self.user6 = mixer.blend(User, is_active=False)
        self.admin = mixer.blend(User, roles=['ADMIN'])

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()
        super().tearDown()

    def test_edit_users_by_anonymous(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user1.guid],
                "action": "ban"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_edit_users_by_user(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid],
                "action": "ban"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    def test_ban_users_by_admin(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid, self.user3.guid],
                "action": "ban"
            }
        }

        self.assertEqual(User.objects.filter(is_active=False).count(), 2)

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editUsers"]["success"], True)
        self.assertEqual(User.objects.filter(is_active=False).count(), 4)

    def test_unban_users_by_admin(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user5.guid],
                "action": "unban"
            }
        }

        self.assertEqual(User.objects.filter(is_active=False).count(), 2)

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editUsers"]["success"], True)
        self.assertEqual(User.objects.filter(is_active=False).count(), 1)

    def test_ban_yourself(self):
        mutation = """
            mutation editUsers($input: editUsersInput!) {
                editUsers(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guids": [self.user2.guid, self.admin.guid],
                "action": "ban"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(mutation, variables)
