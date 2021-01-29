from django.contrib.auth.models import AnonymousUser
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from user.models import User
from core.models import ProfileField, Setting, UserProfileField
from core import config
from mixer.backend.django import mixer
from importlib import import_module
from core.middleware import RedirectMiddleware
from http import HTTPStatus
from django.test import RequestFactory, SimpleTestCase


class RedirectsTestCase(FastTenantTestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.dummy_response = object()
        self.middleware = RedirectMiddleware(lambda request: self.dummy_response)


    def test_redirect(self):
        cache.set("%s%s" % (connection.schema_name, 'REDIRECTS'), {"/path1": "/path2", "/path3": "/path4"})

        request = self.request_factory.get("/path1", HTTP_HOST="www.example.com")

        response = self.middleware(request)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/path2")

        cache.clear()