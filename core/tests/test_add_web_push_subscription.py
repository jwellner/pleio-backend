from core.tests.helpers import PleioTenantTestCase, override_config
from user.factories import UserFactory


class AddWebPushSubscriptionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory()

    def test_add_web_push_subscription(self):
        mutation = """
            mutation AddWebPushSubscription($input: addWebPushSubscriptionInput!) {
                addWebPushSubscription(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "browser": "firefox",
                "endpoint": "service.firefox.test",
                "auth": "auth_key",
                "p256dh": "sfieriu3r3$4re"
            }
        }

        with override_config(PUSH_NOTIFICATIONS_ENABLED=True):
            self.graphql_client.force_login(self.user1)
            result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertIsNotNone(data["addWebPushSubscription"]["success"], True)
