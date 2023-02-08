from http import HTTPStatus
from unittest import mock

from django.conf import settings

from control.models import AccessCategory, AccessLog
from control.tests.helpers import Control as _


class TestViewDownloadBackupTestCase(_.BaseTestCase):

    @mock.patch("control.views.os.path.isfile")
    @mock.patch("tenants.models.ClientManager.get")
    def test_anonymous_visitor(self, client_get, isfile):
        expected_backup_filename = "backup_filename.zip"
        isfile.return_value = True
        client_get.return_value = mock.MagicMock()

        response = self.client.get(_.reverse("download_backup", args=[1, expected_backup_filename]))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(isfile.call_count, 0)

    @mock.patch("control.views.os.path.isfile")
    @mock.patch("tenants.models.ClientManager.get")
    def test_download_backup_not_a_zipfile(self, client_get, isfile):
        expected_schema = "demo"
        isfile.return_value = False
        client_get.return_value = mock.MagicMock()
        client_get.return_value.schema_name = expected_schema

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_backup", args=[1, f"_{expected_schema}"]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @mock.patch("control.views.os.path.isfile")
    @mock.patch("tenants.models.ClientManager.get")
    def test_download_backup_not_a_file(self, client_get, isfile):
        expected_schema = "demo"
        isfile.return_value = False
        client_get.return_value = mock.MagicMock()
        client_get.return_value.schema_name = expected_schema

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_backup", args=[1, f"_{expected_schema}.zip"]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @mock.patch("control.models.AccessLogManager.create")
    @mock.patch("control.views.mimetypes.guess_type")
    @mock.patch("control.views.os.path.isfile")
    @mock.patch("tenants.models.ClientManager.get")
    def test_download_backup_is_a_file(self, client_get, isfile, guess_type, accesslog_create):
        import os.path
        expected_backup_filename = "backup_demo.zip"
        isfile.return_value = True
        client_get.return_value = mock.MagicMock()
        client_get.return_value.schema_name = 'demo'
        guess_type.return_value = "application/zip"
        self.diskfile_factory(os.path.join(settings.BACKUP_PATH, expected_backup_filename), "Demo file\n")

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_backup", args=[1, expected_backup_filename]))
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(content, b"Demo file\n")
        self.assertEqual(accesslog_create.call_args.kwargs, {
            "category": AccessLog.custom_category(AccessCategory.SITE_BACKUP, 1),
            "item_id": expected_backup_filename,
            "type": AccessLog.AccessTypes.DOWNLOAD,
            "user": self.admin,
        })

