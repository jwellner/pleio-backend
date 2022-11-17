from django.db import connection, connections
from django.test import TestCase, override_settings
from django_tenants.utils import schema_context
from django.conf import settings
from unittest import mock

TEST_DATABASES = settings.DATABASES
TEST_DATABASES["replica"] = settings.DATABASES["default"]

test_settings = override_settings(
    DATABASES=TEST_DATABASES
)

@test_settings
class SetTenantTestCase(TestCase):
    databases = {'default', 'replica'}

    @mock.patch("django_tenants.postgresql_backend.base.EXTRA_SET_TENANT_METHOD")
    def test_schema_on_replica_without_extra_tenant_command(self, mock_extra_set_tenant_method_path):
        with schema_context('test_1'):
            mock_extra_set_tenant_method_path.assert_called()
            self.assertEqual(connection.schema_name, 'test_1')
            self.assertNotEqual(connections["replica"].schema_name, 'test_1')

    def test_schema_on_replica_with_extra_tenant_command(self):
        with schema_context('test_2'):
            self.assertEqual(connection.schema_name, 'test_2')
            self.assertEqual(connections["replica"].schema_name, 'test_2')

            with schema_context('test_3'):
                self.assertEqual(connection.schema_name, 'test_3')
                self.assertEqual(connections["replica"].schema_name, 'test_3')

            self.assertEqual(connection.schema_name, 'test_2')
            self.assertEqual(connections["replica"].schema_name, 'test_2')

        with schema_context('test_4'):
            self.assertEqual(connection.schema_name, 'test_4')
            self.assertEqual(connections["replica"].schema_name, 'test_4')

        self.assertEqual(connection.schema_name, 'public')
        self.assertEqual(connections["replica"].schema_name, 'public')
