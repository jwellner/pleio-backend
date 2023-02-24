from unittest import mock

from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase


class TestSiteInfoView(PleioTenantTestCase):

    def test_url_spec(self):
        self.assertEqual('/api/site_info/', reverse('site_info'))

    def test_anonymous(self):
        response = self.client.get(reverse("site_info"))
        self.assertEqual(400, response.status_code)

    @mock.patch('concierge.views.tenant_summary')
    @mock.patch('concierge.views.ApiTokenData.assert_valid')
    def test_authenticated(self, mocked_assert_valid, mocked_tenant_summary):
        mocked_tenant_summary.return_value = {"data": "testing"}
        response = self.client.get(reverse("site_info"))

        self.assertEqual(200, response.status_code)
        self.assertTrue(mocked_assert_valid.called)
        self.assertTrue(mocked_tenant_summary.called)
        self.assertDictEqual(response.json(), mocked_tenant_summary.return_value)
