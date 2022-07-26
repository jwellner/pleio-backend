from control.tasks import get_db_disk_usage, get_file_disk_usage
from core.models import SiteStat
from tenants.helpers import FastTenantTestCase


class TestTaskGetDiskUsageTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        SiteStat.objects.create(stat_type='DB_SIZE', value="11")
        SiteStat.objects.create(stat_type='DISK_SIZE', value="22")

    def test_get_db_disk_usage(self):
        result = get_db_disk_usage(self.tenant.schema_name)
        self.assertEqual(11, result)

    def test_get_file_disk_usage(self):
        result = get_file_disk_usage(self.tenant.schema_name)
        self.assertEqual(22, result)
