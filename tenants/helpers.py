import os
from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase as BaseFastTenantTestCase
from django_tenants.test.client import TenantClient

from tenants.models import Client


class FastTenantTestCase(BaseFastTenantTestCase):
    tenant: Client = None
    client: TenantClient = None

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

    def create_tenant_folder(self, folder):
        path = os.path.join(f"%s/%s" % (settings.MEDIA_ROOT, connection.schema_name), folder)
        os.makedirs(path, exist_ok=True)
        return path
