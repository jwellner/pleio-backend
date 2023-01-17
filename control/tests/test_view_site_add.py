from http import HTTPStatus
from unittest import mock

from control.tests.helpers import Control as _


class TestViewSiteAddTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("site_add"))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "sites_add.html")

    def test_add_site_form(self):
        self.client.force_login(self.admin)

        response = self.client.get(_.reverse("site_add"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sites_add.html")

    @mock.patch("control.models.TaskManager.create_task")
    def test_add_site_submit(self, create_task):
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_add"), data={
            "schema_name": "new_site",
            "domain": "new.site",
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("sites"))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.args, ('control.tasks.add_site', ('new_site', 'new.site')))

    @mock.patch("control.models.TaskManager.create_task")
    def test_add_site_submit_from_backup(self, create_task):
        self.client.force_login(self.admin)

        response = self.client.post(_.reverse("site_add"), data={
            "schema_name": "new_site",
            "domain": "new.site",
            "backup": "some_backup_YYYYmmdd",
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("sites"))
        self.assertEqual(create_task.call_count, 1)
        self.assertEqual(create_task.call_args.args, ('control.tasks.restore_site', ('some_backup_YYYYmmdd', 'new_site', 'new.site')))
