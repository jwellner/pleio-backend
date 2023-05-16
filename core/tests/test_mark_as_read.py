from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from notifications.signals import notify


class MarkAsReadTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

    def tearDown(self):
        super().tearDown()

    def test_mark_as_read_user_anon(self):
        mutation = """
            mutation Notification($input: markAsReadInput!) {
                markAsRead(input: $input) {
                    success
                    notification {
                    id
                    isUnread
                    __typename
                    }
                    __typename
                }
            }

        """
        notificationid = 1
        variables = {
            "input": {
                "id": notificationid
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_mark_as_read(self):
        mutation = """
            mutation Notification($input: markAsReadInput!) {
                markAsRead(input: $input) {
                    success
                    notification {
                    id
                    isUnread
                    __typename
                    }
                    __typename
                }
            }

        """
        notification = notify.send(self.user1, recipient=self.user1, verb='welcome')[0][1][0]
        variables = {
            "input": {
                "id": notification.id
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["markAsRead"]["success"], True)
        self.assertEqual(data["markAsRead"]["notification"]["isUnread"], False)
        self.assertEqual(data["markAsRead"]["notification"]["id"], notification.id)
