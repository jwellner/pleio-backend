from http import HTTPStatus
from unittest import mock

from django_tenants.utils import get_tenant_model

from control.tests.helpers import Control as _


class TestViewSiteBackupTestCase(_.BaseTestCase):

    @mock.patch("control.views.localtime")
    def test_backup_folder(self, localtime):
        site = mock.MagicMock(spec=get_tenant_model())
        site.schema_name = "SCHEMA"
        mocked_time = mock.MagicMock()
        mocked_time.strftime.return_value = "TIMESTAMP"
        localtime.return_value = mocked_time

        from control.views import _backup_folder
        folder = _backup_folder(site)

        self.assertEqual(folder, "timestamp_schema")

    @mock.patch("tenants.models.ClientManager.get")
    def test_anonymous_visitor(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        response = self.client.get(_.reverse("site_backup", args=[1]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites_backup.html")
        self.assertEqual(manager_get.call_count, 0)

    @mock.patch("tenants.models.ClientManager.get")
    def test_backup_site_form(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("site_backup", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites_backup.html")

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.models.TaskManager.create_task")
    @mock.patch("control.views._backup_folder")
    def test_enable_site_submit_with_files(self, backup_folder, create_task, manager_get):
        backup_folder.return_value = "BACKUP_FOLDER"
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_backup", args=[1]), data={
            'include_files': True,
        })

        self.maxDiff = None

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("site_backup", args=[1]))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.kwargs, {"name": 'control.tasks.backup_site',
                                                        "arguments": (1, False, "BACKUP_FOLDER", False),
                                                        "origin": "site_backup:1",
                                                        "author": response.wsgi_request.user,
                                                        "followup": "core.tasks.followup_backup_complete",
                                                        "client": site})

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.models.TaskManager.create_task")
    @mock.patch("control.views._backup_folder")
    def test_enable_site_submit_to_archive(self, backup_folder, create_task, manager_get):
        backup_folder.return_value = "BACKUP_FOLDER"
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_backup", args=[1]), data={
            'create_archive': True,
        })

        self.maxDiff = None

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("site_backup", args=[1]))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.kwargs, {"name": 'control.tasks.backup_site',
                                                        "arguments": (1, True, "BACKUP_FOLDER", True),
                                                        "origin": "site_backup:1",
                                                        "author": response.wsgi_request.user,
                                                        "followup": "core.tasks.followup_backup_complete",
                                                        "client": site})
