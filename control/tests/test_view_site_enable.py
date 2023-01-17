from http import HTTPStatus
from unittest import mock

from django_tenants.utils import get_tenant_model

from control.tests.helpers import Control as _


class TestViewSiteEnableTestCase(_.BaseTestCase):

    @mock.patch("tenants.models.ClientManager.get")
    def test_anonymous_visitor(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        response = self.client.get(_.reverse("site_enable", args=[1]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites_enable.html")
        self.assertEqual(manager_get.call_count, 0)

    @mock.patch("tenants.models.ClientManager.get")
    def test_enable_site_form(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("site_enable", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites_enable.html")

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("control.models.TaskManager.create_task")
    def test_enable_site_submit(self, create_task, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_enable", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("sites"))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.args, ('control.tasks.update_site', (1, {"is_active": True})))
