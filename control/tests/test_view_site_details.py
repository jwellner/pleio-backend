from http import HTTPStatus

from control.tests.helpers import Control as _
from core.tests.helpers import suppress_stdout
from control.views import Client


class TestViewSiteDetailsTestCase(_.BaseTestCase):

    @suppress_stdout()
    def setUp(self):
        super().setUp()
        self.demo, _ = Client.objects.get_or_create(schema_name="demo1")

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("site_details", args=[self.demo.id]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "site.html")

    def test_site_details(self):
        self.client.force_login(self.admin)

        response = self.client.get(_.reverse("site_details", args=[self.demo.id]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "site.html")
