from django.conf import settings
from django.db import connection
from django_tenants.utils import get_tenant_model
from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class Control:

    @staticmethod
    def reverse(*args, **kwargs):
        return reverse(*args, urlconf="control.urls", **kwargs)

    class BaseTestCase(PleioTenantTestCase):

        @classmethod
        def get_test_schema_name(cls):
            return 'public'

        @classmethod
        def get_test_tenant_domain(cls):
            return 'admin.test.com'

        def setUp(self):
            super().setUp()
            connection.set_schema_to_public()
            self.override_setting(
                AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'],
                LOGIN_URL='/admin/login/',
                MIDDLEWARE=[mc for mc in settings.MIDDLEWARE
                            if mc not in settings.TENANT_MIDDLEWARE]
            )
            self.public_tenant = get_tenant_model().objects.get(schema_name='public')
            self.admin = UserFactory(is_superadmin=True)

        def tearDown(self):
            self.admin.delete()
            super().tearDown()
