from django_tenants.utils import schema_context

from control.tasks import get_sites_admin
from core.tests.helpers import suppress_stdout
from tenants.helpers import FastTenantTestCase
from user.factories import AdminFactory


class TestTaskGetSitesAdminTestCase(FastTenantTestCase):
    @suppress_stdout()
    def setUp(self):
        super().setUp()

        self.USERNAME = 'Demo user'
        self.EMAIL = 'demo.user@example.com'
        self.TENANT_DOMAIN = self.tenant.primary_domain
        self.TENANT_ID = self.tenant.id

        AdminFactory(name=self.USERNAME,
                     email=self.EMAIL)

    @schema_context('public')
    def test_get_sites_admin(self):
        result = get_sites_admin()

        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], {
            "name": self.USERNAME,
            "email": self.EMAIL,
            "client_id": self.TENANT_ID,
            "client_domain": self.TENANT_DOMAIN
        })
