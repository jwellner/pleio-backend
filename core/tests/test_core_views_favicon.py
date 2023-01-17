from django.http import HttpRequest

from core.tests.helpers import PleioTenantTestCase
from core.views import favicon


class TestCoreViewsFaviconTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    def test_default_favicon(self):
        self.override_config(FAVICON=None)
        response = favicon(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/static/apple-touch-icon.png")

    def test_custom_favicon(self):
        self.override_config(FAVICON="/custom/favicon.ico")
        response = favicon(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/custom/favicon.ico")

