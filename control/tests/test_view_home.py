from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewHomeTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("home"))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, '/admin/login/?next=/')

    def test_non_admin_visitor(self):
        self.admin.is_superadmin = False
        self.admin.save()

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("home"))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, '/admin/login/?next=/')

    def test_admin_visitor(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse('home'))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "home.html")
