from http import HTTPStatus
from unittest import mock

from django_tenants.utils import get_tenant_model

from control.tests.helpers import Control as _


class TestViewSiteDeleteTestCase(_.BaseTestCase):

    @mock.patch("tenants.models.ClientManager.get")
    def test_anonymous_visitor(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site

        response = self.client.get(_.reverse("site_delete", args=[1]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites_delete.html")
        self.assertEqual(manager_get.call_count, 0)

    @mock.patch("tenants.models.ClientManager.get")
    def test_add_site_form(self, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        manager_get.return_value = site
        self.client.force_login(self.admin)

        response = self.client.get(_.reverse("site_delete", args=[1]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites_delete.html")

    @mock.patch("tenants.models.ClientManager.get")
    @mock.patch("tenants.models.ClientManager.filter")
    @mock.patch("control.models.TaskManager.create_task")
    def test_delete_site_submit(self, create_task, manager_filter, manager_get):
        site = mock.MagicMock(spec=get_tenant_model())
        site.id = 1
        site.schema_name = 'demo_site'
        manager_get.return_value = site
        filter_result = mock.MagicMock()
        filter_result.first.return_value = site
        manager_filter.return_value = filter_result
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_delete", args=[1]), data={
            "site_id": 1,
            "check": "demo_site",
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("sites"))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.args, ('control.tasks.delete_site', (1,)))
