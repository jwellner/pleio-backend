from django_tenants.test.client import TenantClient
from django.core.cache import cache
from django.db import connection

from core.utils.mail import EmailSettingsTokenizer
from tenants.helpers import FastTenantTestCase
from core.tests.helpers import override_config
from user.models import User
from mixer.backend.django import mixer


class EditEmailSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User, is_active=True)
        self.user.profile.receive_notification_email = True
        self.user.profile.save()
        self.client = TenantClient(self.tenant)

    @override_config(IS_CLOSED=False)
    def test_edit_site_settings(self):
        signer = EmailSettingsTokenizer()
        response = self.client.get(signer.create_url(self.user))

        self.assertTemplateUsed(response, 'edit_email_settings.html')

    @override_config(IS_CLOSED=False)
    def test_edit_site_settings_false_token(self):
        signer = EmailSettingsTokenizer()
        url = signer.create_url(self.user)

        response = self.client.get(url + 'a')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    @override_config(IS_CLOSED=False)
    def test_edit_site_settings_change_settings(self):
        signer = EmailSettingsTokenizer()
        url = signer.create_url(self.user)

        data = {
            "overview_email_enabled": "monthly"
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.receive_notification_email, False)
        self.assertEqual(self.user.profile.overview_email_interval, 'monthly')
