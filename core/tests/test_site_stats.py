from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection

from core.tasks import save_db_disk_usage, save_file_disk_usage
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from mixer.backend.django import mixer
from user.models import User


class SiteStatsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        csv_bytes = (
            b'aap;row-1-2@example.com;row-1-3;row-1-4;row-1-5\n'
            b'noot;row-2-2@example.com;row-2-3;row-2-4;row-2-5\n'
            b'mies;row-3-2@example.com;row-3-3;row-3-4;row-3-5'
        )

        upload = SimpleUploadedFile('test.csv', csv_bytes)

        self.admin = mixer.blend(User, roles=['ADMIN'], is_delete_requested=False)
        self.file = mixer.blend(FileFolder, upload=upload)
        self.query = """
            query SiteStats {
                siteStats {
                    dbUsage
                    fileDiskUsage
                }
            }
        """

    def test_site_settings_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["siteStats"]["dbUsage"], 0)
        self.assertEqual(data["siteStats"]["fileDiskUsage"], 0)

        save_db_disk_usage.s(connection.schema_name).apply()
        save_file_disk_usage.s(connection.schema_name).apply()

        result = self.graphql_client.post(self.query, {})
        data = result["data"]

        self.assertNotEqual(data["siteStats"]["dbUsage"], 0)
        self.assertNotEqual(data["siteStats"]["fileDiskUsage"], 0)
