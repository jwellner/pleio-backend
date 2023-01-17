from http import HTTPStatus

from control.tests.helpers import Control as _
from control.views import Client


class TestViewSiteDetailsTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        tenant = Client.objects.get(schema_name="fast_test")

        response = self.client.get(_.reverse("site_details", args=[tenant.id]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "site.html")

    def test_site_details(self):
        tenant = Client.objects.get(schema_name="fast_test")
        self.client.force_login(self.admin)

        response = self.client.get(_.reverse("site_details", args=[tenant.id]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "site.html")
