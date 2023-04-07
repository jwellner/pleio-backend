from unittest import mock

from django.http import HttpRequest
from django.urls import reverse

from concierge.views import ban_user
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestApiBanUserTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(email="known@example.com")
        self.api_token_data = type("ApiTokenData", (object,), {
            "data": {
                "email": self.user.email,
                "id": "42",
                "reason": "Foo",
            },
            "assert_valid": lambda: True
        })

    @mock.patch("concierge.views.ApiTokenData")
    def test_ban_unknown_user(self, api_token_data_factory):
        self.unknown_mail = "unknown@example.com"

        self.api_token_data.data['email'] = "unknown@example.com"
        api_token_data_factory.return_value = self.api_token_data

        response = self.client.post(reverse("profile_banned"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": "OK"})

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.ban_reason, "")

    @mock.patch("concierge.views.ApiTokenData")
    def test_ban_known_user(self, api_token_data_factory):
        api_token_data_factory.return_value = self.api_token_data

        response = self.client.post(reverse("profile_banned"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": "OK"})

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.ban_reason, "Foo")

    def test_ban_user_via_get_request(self):
        response = self.client.get(reverse("profile_banned"))
        self.assertEqual(response.status_code, 400)

    @mock.patch("concierge.views.ApiTokenData")
    def test_ban_user_invalid_data(self, api_token_data_factory):
        def assert_valid():
            raise AssertionError()

        api_token_data_factory.return_value = self.api_token_data
        self.api_token_data.assert_valid = assert_valid

        response = self.client.post(reverse("profile_banned"))
        self.assertEqual(response.status_code, 400)
