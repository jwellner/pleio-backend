from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from django.core.cache import cache
from django.db import connection

class AddWebPushSubscriptionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory()
        cache.set("%s%s" % (connection.schema_name, 'PUSH_NOTIFICATIONS_ENABLED'), True)

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

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertIsNotNone(data["addWebPushSubscription"]["success"], True)
