import os
from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase as BaseFastTenantTestCase
from django_tenants.test.client import TenantClient
from unittest import mock

from tenants.models import Client


class FastTenantTestCase(BaseFastTenantTestCase):
    tenant: Client = None
    client: TenantClient = None

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        mock.patch("logging.Logger.warning").start()
        mock.patch("warnings.warn").start()

    def tearDown(self) -> None:
        mock.patch.stopall()
        super().tearDown()

    def create_tenant_folder(self, folder):
        path = os.path.join(f"%s/%s" % (settings.MEDIA_ROOT, connection.schema_name), folder)
        os.makedirs(path, exist_ok=True)
        return path


def switch_schema(schema_name):
    from django.db import connections
    from django_tenants.utils import get_tenant_database_alias
    tenant = Client.objects.get(schema_name=schema_name)
    connection = connections[get_tenant_database_alias()]
    connection.set_tenant(tenant)
