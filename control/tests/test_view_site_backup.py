import uuid
from http import HTTPStatus
from unittest import mock

from django_tenants.utils import get_tenant_model

from control.tests.helpers import Control as _


class TestViewSiteBackupTestCase(_.BaseTestCase):

    def setUp(self):
        super().setUp()

    @mock.patch("tenants.models.ClientManager.get")
    def test_anonymous_visitor(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        response = self.client.get(_.reverse("site_backup", args=[1]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites_backup.html")
        self.assertEqual(manager_get.call_count, 0)

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.views.schema_config")
    def test_backup_site_form(self, schema_config, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        site.schema_name = "demo"
        site.id = 1
        manager_get.return_value = site
        schema_config.return_value = "Demo site"

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("site_backup", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites_backup.html")

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.views.schema_config")
    @mock.patch("control.views.schedule_backup")
    def test_enable_site_submit_with_files(self, schedule_backup, schema_config, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        site.schema_name = "demo"
        site.id = 1
        manager_get.return_value = site
        schema_config.return_value = "Demo Site"
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_backup", args=[1]), data={
            'include_files': True,
        })

        self.maxDiff = None

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("site_backup", args=[1]))
        self.assertEqual(schedule_backup.call_count, 1)
        self.assertEqual(schedule_backup.call_args.args,
                         (site, self.admin, True, False))

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.views.schema_config")
    @mock.patch("control.views.schedule_backup")
    def test_enable_site_submit_to_archive(self, schedule_backup, schema_config, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        site.schema_name = "demo"
        site.id = 1
        manager_get.return_value = site
        schema_config.return_value = "Demo Site"

        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_backup", args=[1]), data={
            'create_archive': True,
        })

        self.maxDiff = None

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("site_backup", args=[1]))
        self.assertEqual(schedule_backup.call_count, 1)
        self.assertEqual(schedule_backup.call_args.args,
                         (site, self.admin, False, True))
