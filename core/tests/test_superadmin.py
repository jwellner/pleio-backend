from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from user.models import User
from mixer.backend.django import mixer
from django.core.cache import cache
from django.db import connection

class SuperadminTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.user = mixer.blend(User, is_active=True)
        self.user_admin = mixer.blend(User, is_active=True, roles=['ADMIN'])
        self.user_superadmin = mixer.blend(User, is_active=True, is_superadmin=True)

        self.client = TenantClient(self.tenant)

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_anonymous(self):

        response = self.client.get('/superadmin', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_user(self):

        self.client.force_login(self.user)
        response = self.client.get('/superadmin', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_admin(self):
        self.client.force_login(self.user_admin)

        response = self.client.get('/superadmin', follow=True)

        self.assertTemplateUsed(response, 'react.html')

    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_superadmin(self):

        self.client.force_login(self.user_superadmin)

        response = self.client.get('/superadmin', follow=True)

        self.assertTemplateUsed(response, 'superadmin/home.html')
