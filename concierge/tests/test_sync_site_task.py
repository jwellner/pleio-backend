from unittest import mock

from django.test import override_settings

from tenants.helpers import FastTenantTestCase


class TestSyncSiteTestCase(FastTenantTestCase):

    @mock.patch("concierge.tasks.api_sync_site")
    def test_sync_site(self, mocked_sync_site):
        # pylint: disable=import-outside-toplevel
        from concierge.tasks import sync_site
        sync_site(self.tenant.schema_name)

        self.assertTrue(mocked_sync_site.called)
