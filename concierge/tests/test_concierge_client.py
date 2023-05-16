from unittest import mock
from concierge.api import ConciergeClient
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestFetchAvatarTestCase(PleioTenantTestCase):
    EMAIL = "info@example.com"
    EXTERNAL_ID = 1
    CLIENT_ID = 10
    CLIENT_SECRET = 100
    ERROR_REASON = "Reason for error"
    ERROR_STATUS = 4000
    ACCOUNT_URL = 'https://demo/'
    API_RESOURCE = 'demo-resource'
    API_DATA = {"foo": "bar"}

    def setUp(self):
        super().setUp()

        self.override_setting(ACCOUNT_API_URL=self.ACCOUNT_URL,
                              OIDC_RP_CLIENT_ID=self.CLIENT_ID,
                              OIDC_RP_CLIENT_SECRET=self.CLIENT_SECRET)
        self.user = UserFactory(email=self.EMAIL,
                                external_id=self.EXTERNAL_ID)

    def tearDown(self):
        super().tearDown()

    @mock.patch("concierge.api.requests.get")
    def test_fetch(self, mocked_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = None
        json_response = mock.MagicMock()
        mock_response.json.return_value = json_response
        mocked_get.return_value = mock_response

        self.mocked_log_warning.reset_mock()
        client = ConciergeClient(self.API_RESOURCE)
        response = client.fetch(self.API_RESOURCE)

        self.assertTrue(mock_response.json.called)
        self.assertFalse(self.mocked_log_warning.called)
        self.assertEqual(response, json_response)
        self.assertTrue(client.is_ok())
        self.assertEqual(client.reason, '')

        self.assertEqual(mocked_get.call_args.args, ('https://demo/demo-resource',))
        self.assertEqual(mocked_get.call_args.kwargs, {'headers': {'x-oidc-client-id': self.CLIENT_ID,
                                                                   'x-oidc-client-secret': self.CLIENT_SECRET},
                                                       'timeout': 30})

    @mock.patch("concierge.api.requests.get")
    def test_fetch_avatar_with_error(self, mocked_get):
        mock_response = mock.MagicMock()
        mock_response.ok = False
        mock_response.status_code = self.ERROR_STATUS
        mock_response.reason = self.ERROR_REASON
        mocked_get.return_value = mock_response

        self.mocked_log_warning.reset_mock()
        client = ConciergeClient(self.API_RESOURCE)
        response = client.fetch(self.API_RESOURCE)
        self.assertFalse(client.is_ok())
        self.assertNotEqual(client.reason, '')

        self.assertTrue(self.mocked_log_warning.called)
        self.assertFalse(mock_response.json.called)
        self.assertEqual(response, {
            'error': self.ERROR_REASON,
            'status_code': self.ERROR_STATUS
        })

    @mock.patch("concierge.api.requests.post")
    def test_post(self, mocked_post):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = None
        json_response = mock.MagicMock()
        mock_response.json.return_value = json_response
        mocked_post.return_value = mock_response

        self.mocked_log_warning.reset_mock()
        client = ConciergeClient(self.API_RESOURCE)
        response = client.post(self.API_RESOURCE, self.API_DATA)

        self.assertTrue(mock_response.json.called)
        self.assertFalse(self.mocked_log_warning.called)
        self.assertEqual(response, json_response)
        self.assertTrue(client.is_ok())
        self.assertEqual(client.reason, '')

        self.assertEqual(mocked_post.call_args.args, ('https://demo/demo-resource',))
        self.assertEqual(mocked_post.call_args.kwargs, {'data': self.API_DATA,
                                                        'headers': {'x-oidc-client-id': self.CLIENT_ID,
                                                                   'x-oidc-client-secret': self.CLIENT_SECRET},
                                                       'timeout': 30})

    @mock.patch("concierge.api.requests.post")
    def test_post_with_error(self, mocked_post):
        mock_response = mock.MagicMock()
        mock_response.ok = False
        mock_response.status_code = self.ERROR_STATUS
        mock_response.reason = self.ERROR_REASON
        mocked_post.return_value = mock_response

        self.mocked_log_warning.reset_mock()
        client = ConciergeClient(self.API_RESOURCE)
        response = client.post(self.API_RESOURCE, self.API_DATA)

        self.assertTrue(self.mocked_log_warning.called)
        self.assertFalse(mock_response.json.called)
        self.assertEqual(response, {
            'error': self.ERROR_REASON,
            'status_code': self.ERROR_STATUS
        })
        self.assertFalse(client.is_ok())
        self.assertNotEqual(client.reason, '')
