from core.tests.helpers import PleioTenantTestCase, override_config


class TestCoreViewsCustomCssTestCase(PleioTenantTestCase):

    def test_login(self):
        response = self.client.get('/login')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/oidc/authenticate/?provider=pleio")

    @override_config(OIDC_PROVIDERS=[0, 1])
    def test_login_plural_providers(self):
        response = self.client.get('/login')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")


