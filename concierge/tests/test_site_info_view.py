from unittest import mock

from django.urls import reverse

from core import override_local_config
from core.tests.helpers import PleioTenantTestCase


class TestSiteInfoView(PleioTenantTestCase):

    def test_url_spec(self):
        self.assertEqual('/api/site_info/', reverse('site_info'))

    def test_anonymous(self):
        response = self.client.get(reverse("site_info"))
        self.assertEqual(403, response.status_code)

    @override_local_config(TENANT_API_TOKEN="for-testing")
    @mock.patch('concierge.views.tenant_summary')
    def test_authenticated(self, mocked_tenant_summary):
        mocked_tenant_summary.return_value = {"data": "testing"}
        response = self.client.get(reverse("site_info"), HTTP_x_origin_site_api_token='for-testing')

        self.assertEqual(200, response.status_code)
        self.assertTrue(mocked_tenant_summary.called)
        self.assertDictEqual(response.json(), mocked_tenant_summary.return_value)
