from control.tasks import get_sites
from core.lib import tenant_schema
from tenants.helpers import FastTenantTestCase


class TestTaskGetSitesTestCase(FastTenantTestCase):

    def test_get_sites(self):
        sites = get_sites()

        site_names = [site['name'] for site in sites]
        self.assertEqual(len(sites), 1)
        self.assertIn(tenant_schema(), site_names)

        self.assertIn('id', sites[0])
        self.assertIn('name', sites[0])
        self.assertIn('is_active', sites[0])
        self.assertIn('domain', sites[0])
