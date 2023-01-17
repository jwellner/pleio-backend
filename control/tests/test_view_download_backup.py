from http import HTTPStatus
from unittest import mock

from django.conf import settings

from control.tests.helpers import Control as _


class TestViewDownloadBackupTestCase(_.BaseTestCase):

    @mock.patch("control.views.os.path.isfile")
    @mock.patch("control.models.TaskManager.get")
    def test_anonymous_visitor(self, task_get, isfile):
        expected_backup_filename = "backup_filename.zip"
        isfile.return_value = True
        task_get.return_value = mock.MagicMock()
        task_get.return_value.response = expected_backup_filename

        response = self.client.get(_.reverse("download_backup", args=[1]))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(isfile.call_count, 0)

    @mock.patch("control.views.os.path.isfile")
    @mock.patch("control.models.TaskManager.get")
    def test_download_backup_not_a_file(self, task_get, isfile):
        task_get.return_value = mock.MagicMock()
        task_get.return_value.response = "backup_filename"
        isfile.return_value = False

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_backup", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @mock.patch("logging.Logger.info")
    @mock.patch("control.views.mimetypes.guess_type")
    @mock.patch("control.views.os.path.isfile")
    @mock.patch("control.models.TaskManager.get")
    def test_download_backup_is_a_file(self, task_get, isfile, guess_type, logger_info):
        import os.path
        expected_backup_filename = "backup_filename.zip"
        isfile.return_value = True
        task_get.return_value = mock.MagicMock()
        task_get.return_value.response = expected_backup_filename
        guess_type.return_value = "application/zip"
        self.diskfile_factory(os.path.join(settings.BACKUP_PATH, expected_backup_filename), "Demo file\n")

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_backup", args=[1]))
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(content, b"Demo file\n")
        self.assertEqual(logger_info.call_args.args, ('download_backup %s by %s', expected_backup_filename, self.admin.email))

