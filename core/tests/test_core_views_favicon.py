from django.http import HttpRequest

from core.tests.helpers import PleioTenantTestCase, override_config
from core.views import favicon


class TestCoreViewsFaviconTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    @override_config(FAVICON=None)
    def test_default_favicon(self):
        response = favicon(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/static/apple-touch-icon.png")

    @override_config(FAVICON="/custom/favicon.ico")
    def test_custom_favicon(self):
        response = favicon(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/custom/favicon.ico")

