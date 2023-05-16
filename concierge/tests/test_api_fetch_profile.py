from unittest import mock

from concierge.api import fetch_profile
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestFetchProfileTestCase(PleioTenantTestCase):
    EMAIL = "info@example.com"
    EXTERNAL_ID = 1

    def setUp(self):
        super().setUp()

        self.user = UserFactory(email=self.EMAIL,
                                external_id=self.EXTERNAL_ID)

    def tearDown(self):
        super().tearDown()

    @mock.patch("concierge.api.ConciergeClient.fetch")
    def test_fetch_profile(self, mocked_fetch):
        mock_response = mock.MagicMock()
        mocked_fetch.return_value = mock_response

        self.mocked_warn.reset_mock()
        response = fetch_profile(self.user)

        self.assertFalse(self.mocked_warn.called)
        self.assertEqual(mocked_fetch.call_args.args, ('/api/users/fetch_profile/1',))

    @mock.patch("concierge.api.ConciergeClient.fetch")
    def test_fetch_profile_without_external_id(self, mocked_fetch):
        mock_response = mock.MagicMock()
        mocked_fetch.return_value = mock_response

        self.mocked_log_warning.reset_mock()
        self.user.external_id = None
        response = fetch_profile(self.user)

        self.assertTrue(self.mocked_log_warning.called)
        self.assertFalse(mocked_fetch.called)
        self.assertEqual(response, {'error': 'No external ID found yet'})
