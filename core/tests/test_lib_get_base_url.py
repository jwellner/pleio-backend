from unittest import mock

from django.test import override_settings

from core.lib import get_base_url
from core.tests.helpers import PleioTenantTestCase


class TestLibGetBaseUrlTestCase(PleioTenantTestCase):

    def test_local_base_url(self):
        with override_settings(ENV="local"):
            self.assertEqual(get_base_url(), "http://%s:8000" % self.tenant.primary_domain)

    def test_secure_base_url(self):

        with override_settings(ENV="not_local"):
            self.assertEqual(get_base_url(), "https://%s" % self.tenant.primary_domain)

    @mock.patch("tenants.models.ClientManager.get")
    def test_error_at_base_url(self, manager_get):
        manager_get.side_effect = AttributeError()
        self.assertEqual(get_base_url(), "")
