from django.http import HttpRequest

from core.tests.helpers import PleioTenantTestCase, override_config
from core.views import custom_css


class TestCoreViewsCustomCssTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    @override_config(CUSTOM_CSS="Custom CSS")
    def test_default_custom_css(self):
        response = custom_css(self.request)
        content = response.getvalue()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content.decode(), 'Custom CSS')
        self.assertEqual(response.headers['Content-Type'], "text/css")

