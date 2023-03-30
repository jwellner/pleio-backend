from unittest import mock
from concierge.api import sync_site
from core.lib import tenant_summary
from core.tests.helpers import PleioTenantTestCase


class TestSyncSiteTestCase(PleioTenantTestCase):

    @mock.patch("concierge.api.ConciergeClient.post")
    def test_sync_site(self, mocked_post):
        mock_response = mock.MagicMock()
        mocked_post.return_value = mock_response

        self.mocked_warn.reset_mock()
        response = sync_site()

        self.assertFalse(self.mocked_warn.called)
        self.assertEqual(response, mock_response)
        self.assertEqual(mocked_post.call_args.args, ('/api/users/update_origin_site',
                                                      {f"origin_site_{key}": value for key, value in tenant_summary().items()}))
