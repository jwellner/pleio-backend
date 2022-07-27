from django_tenants.test.cases import FastTenantTestCase as BaseFastTenantTestCase
from django_tenants.test.client import TenantClient

from tenants.models import Client


class FastTenantTestCase(BaseFastTenantTestCase):
    tenant: Client = None
    client: TenantClient = None

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
