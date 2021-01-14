from django.contrib.auth.models import AnonymousUser
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from user.models import User
from core.models import ProfileField, Setting, UserProfileField
from mixer.backend.django import mixer
from importlib import import_module

class OnboardingTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        self.existing_user = mixer.blend(User, is_active=True)

        self.profile_field1 = ProfileField.objects.create(
            key="profile_field1",
            name="profile_field1_name",
            is_mandatory=True,
            is_in_onboarding=True
        )

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'), [
            {"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}
        ])

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), True)

        self.client = TenantClient(self.tenant)

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect(self):
        session = self.client.session
        session['onboarding_claims'] = {
            'email': 'test@pleio.nl',
            'name': 'test user'
        }
        session.save()

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)

        response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_create_user(self):
        session = self.client.session

        session['onboarding_claims'] = {
            'email': 'test@pleio.nl',
            'name': 'test user',
            'picture': None,
            'is_government': False,
            'has_2fa_enabled': True,
            'sub': '1234',
            'is_superadmin': False
        }
        session.save()

        response = self.client.post(
            "/onboarding", data={self.profile_field1.guid: "Field1 value"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

        new_user = User.objects.filter(external_id="1234").first()
        self.assertEqual(new_user.email, 'test@pleio.nl')
        self.assertEqual(new_user.has_2fa_enabled, True)

        user_profile_field = UserProfileField.objects.filter(user_profile=new_user.profile, profile_field=self.profile_field1).first()
        self.assertEqual(user_profile_field.value, 'Field1 value')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_no_claim(self):

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)

        response = self.client.get('/onboarding', follow=True)

        self.assertTemplateUsed(response, 'base_closed.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect_existing_off(self):
        self.client.force_login(self.existing_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_FORCE_EXISTING_USERS'), False)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_redirect_existing_on(self):
        self.client.force_login(self.existing_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_FORCE_EXISTING_USERS'), True)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_onboarding_off(self):
        self.client.force_login(self.existing_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), False)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')