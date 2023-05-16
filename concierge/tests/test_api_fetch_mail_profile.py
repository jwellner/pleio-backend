from unittest import mock
from concierge.api import fetch_mail_profile
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestFetchMailProfileTestCase(PleioTenantTestCase):
    EMAIL = "info@example.com"

    def setUp(self):
        super().setUp()
        self.user = UserFactory(email=self.EMAIL)

    def tearDown(self):
        super().tearDown()

    @mock.patch("concierge.api.ConciergeClient.fetch")
    def test_fetch_mail_profile(self, mocked_fetch):
        mock_response = mock.MagicMock()
        mocked_fetch.return_value = mock_response

        self.mocked_warn.reset_mock()
        response = fetch_mail_profile(self.user)

        self.assertFalse(self.mocked_warn.called)
        self.assertEqual(response, mock_response)
        self.assertEqual(mocked_fetch.call_args.args, ('/api/users/fetch_profile_mail/info@example.com',))
