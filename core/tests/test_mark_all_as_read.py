from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class MarkAllAsReadTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        super().tearDown()

    def test_mark_all_as_read_user_anon(self):
        mutation = """
            mutation NotificationsTop($input: markAllAsReadInput!) {
                markAllAsRead(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {}
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_mark_all_as_read(self):
        mutation = """
            mutation NotificationsTop($input: markAllAsReadInput!) {
                markAllAsRead(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {}
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["markAllAsRead"]["success"], True)
