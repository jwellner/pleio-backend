from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import SiteStat
from file.models import FileFolder
from user.models import User

from backend2.schema import schema
from ariadne import graphql_sync
from core.tasks import save_db_disk_usage,save_file_disk_usage
from django.http import HttpRequest
from mixer.backend.django import mixer
from django.core.files.uploadedfile import SimpleUploadedFile


class SiteStatsTestCase(FastTenantTestCase):

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

    def tearDown(self):
        pass

    def test_site_settings_by_admin(self):

        request = HttpRequest()
        request.user = self.admin

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]


        self.assertEqual(data["siteStats"]["dbUsage"], 0)
        self.assertEqual(data["siteStats"]["fileDiskUsage"], 0)

        save_db_disk_usage.s(connection.schema_name).apply()
        save_file_disk_usage.s(connection.schema_name).apply()

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertNotEqual(data["siteStats"]["dbUsage"], 0)
        self.assertNotEqual(data["siteStats"]["fileDiskUsage"], 0)