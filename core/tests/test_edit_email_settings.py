from django.contrib.auth.models import AnonymousUser
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.core import signing
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from user.models import User
from core.models import ProfileField, Setting, UserProfileField
from mixer.backend.django import mixer
from importlib import import_module

class EditEmailSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User, is_active=True)
        self.user.profile.receive_notification_email = True
        self.user.profile.save()

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.client = TenantClient(self.tenant)


    def test_edit_site_settings(self):

        signer = signing.TimestampSigner()
        token = signer.sign_object({
            "id": str(self.user.id),
            "email": self.user.email
        })

        response = self.client.get('/edit_email_settings/' + token, follow=True)

        self.assertTemplateUsed(response, 'edit_email_settings.html')


    def test_edit_site_settings_false_token(self):

        signer = signing.TimestampSigner()
        token = signer.sign_object({
            "id": str(self.user.id),
            "email": self.user.email
        })

        response = self.client.get('/edit_email_settings/' + token + 'a', follow=True)


    def test_edit_site_settings_change_settings(self):

        signer = signing.TimestampSigner()
        token = signer.sign_object({
            "id": str(self.user.id),
            "email": self.user.email
        })

        data = {
            "overview_email_enabled": "monthly"
        }
        response = self.client.post(
            '/edit_email_settings/' + token, data=data
        )
        
        self.user.refresh_from_db()
        self.assertTemplateUsed(response, 'edit_email_settings.html')
        self.assertEqual(self.user.profile.receive_notification_email, False)
        self.assertEqual(self.user.profile.overview_email_interval, 'monthly')
