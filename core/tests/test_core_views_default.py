from unittest import mock

from core.tests.helpers import PleioTenantTestCase


class TestDefaultViewTestCase(PleioTenantTestCase):

    @mock.patch("core.views.is_schema_public")
    def test_public_schema(self, is_schema_public):
        is_schema_public.return_value = True
        self.override_config(IS_CLOSED=False)

        response = self.client.get('')

        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, 'domain_placeholder.html')

    def test_open_site(self):
        self.override_config(IS_CLOSED=False)

        response = self.client.get('')

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'react.html')

    def test_closed_site(self):
        self.override_config(IS_CLOSED=True)

        response = self.client.get('')

        self.assertEqual(401, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
