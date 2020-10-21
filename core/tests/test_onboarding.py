from django.contrib.auth.models import AnonymousUser
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.core.cache import cache
from django.db import connection
from user.models import User
from core.models import ProfileField, Setting
from mixer.backend.django import mixer

class OnboardingTestCase(FastTenantTestCase):
    def setUp(self):
        super().setUp()

        self.new_user = mixer.blend(User, login_count=None)    
        self.existing_user = mixer.blend(User, login_count=1)

        self.profile_field1 = ProfileField.objects.create(
            key="profile_field1",
            name="profile_field1_name",
            is_mandatory=True,
            is_in_onboarding=True
        )

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'), [
            {"name": "", "profileFieldGuids": [str(self.profile_field1.id)]}
        ])

        self.client = TenantClient(self.tenant)

    def test_onboarding_redirect(self):
        self.client.force_login(self.new_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    def test_onboarding_redirect_existing_off(self):
        self.client.force_login(self.existing_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_FORCE_EXISTING_USERS'), False)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    def test_onboarding_redirect_existing_on(self):
        self.client.force_login(self.existing_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_FORCE_EXISTING_USERS'), True)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'onboarding.html')

    def test_onboarding_off(self):
        self.client.force_login(self.new_user)

        cache.set("%s%s" % (connection.schema_name, 'ONBOARDING_ENABLED'), False)

        response = self.client.get('/', follow=True)

        self.assertTemplateUsed(response, 'react.html')