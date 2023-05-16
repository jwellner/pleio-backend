from unittest import mock

from core.tests.helpers import PleioTenantTestCase, override_config


class TestDefaultViewTestCase(PleioTenantTestCase):

    @override_config(IS_CLOSED=False)
    @mock.patch("core.views.is_schema_public")
    def test_public_schema(self, is_schema_public):
        is_schema_public.return_value = True

        response = self.client.get('')

        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, 'domain_placeholder.html')

    @override_config(IS_CLOSED=False)
    def test_open_site(self):

        response = self.client.get('')

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'react.html')

    @override_config(IS_CLOSED=True)
    def test_closed_site(self):

        response = self.client.get('')

        self.assertEqual(401, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
