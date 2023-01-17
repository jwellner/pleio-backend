from http import HTTPStatus
from unittest import mock

from control.tests.helpers import Control as _
from user.factories import AdminFactory, UserFactory


class TestViewDownloadSiteAdminsTestCase(_.BaseTestCase):

    def setUp(self):
        super().setUp()

        self.site_admin = AdminFactory()
        self.another_site_admin = AdminFactory()
        self.regular_user = UserFactory()

    def tearDown(self):
        self.site_admin.delete()
        self.another_site_admin.delete()
        self.regular_user.delete()

        super().tearDown()

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("download_site_admins"))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    @mock.patch("tenants.models.ClientManager.exclude")
    def test_download_site_admins(self, manager_exclude):
        manager_exclude.return_value = [self.public_tenant]

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("download_site_admins"))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.site_admin.email, content)
        self.assertIn(self.another_site_admin.email, content)
        self.assertNotIn(self.regular_user.email, content)
