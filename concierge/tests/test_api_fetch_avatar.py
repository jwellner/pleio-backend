from unittest import mock
from concierge.api import fetch_avatar
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestFetchAvatarTestCase(PleioTenantTestCase):
    EMAIL = "info@example.com"

    def setUp(self):
        super().setUp()
        self.user = UserFactory(email=self.EMAIL)

    def tearDown(self):
        self.user.delete()
        super().tearDown()

    @mock.patch("concierge.api.ConciergeClient.fetch")
    def test_fetch_avatar(self, mocked_fetch):
        mock_response = mock.MagicMock()
        mocked_fetch.return_value = mock_response

        self.mocked_warn.reset_mock()
        response = fetch_avatar(self.user)

        self.assertFalse(self.mocked_warn.called)
        self.assertEqual(response, mock_response)
        self.assertEqual(mocked_fetch.call_args.args, ('/api/users/fetch_avatar/info@example.com',))
