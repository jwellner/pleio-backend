from django.http import HttpRequest

from core.tests.helpers import PleioTenantTestCase
from core.views import unsupported_browser


class TestCoreViewsUnsupportedBrowserTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    def test_get_unsupported_browser_page(self):
        response = unsupported_browser(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("unsupported_browser.html")
