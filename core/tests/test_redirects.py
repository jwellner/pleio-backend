from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from django.core.cache import cache
from django.db import connection
from core.middleware import RedirectMiddleware
from http import HTTPStatus
from django.test import RequestFactory
from django.test.utils import override_settings
from tenants.models import Domain


class RedirectsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()
        self.dummy_response = object()
        self.redirect_middleware = RedirectMiddleware(lambda request: self.dummy_response)

        self.seconday_domain = Domain.objects.create(
            domain='secondary.test.com',
            tenant=self.tenant,
            is_primary=False
        )
        self.client = TenantClient(self.tenant)

    def test_redirect(self):
        cache.set("%s%s" % (connection.schema_name, 'REDIRECTS'), {"/path1": "/path2", "/path3": "/path4"})

        request = self.request_factory.get("/path1", HTTP_HOST="www.example.com")

        response = self.redirect_middleware(request)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/path2")

        request = self.request_factory.get("/path3", HTTP_HOST="www.example.com")

        response = self.redirect_middleware(request)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/path4")

        cache.clear()

    @override_settings(ALLOWED_HOSTS="['*']")
    def test_secondary_domain_redirect(self):

        response = self.client.get('/', HTTP_HOST=self.seconday_domain.domain)

        response_url = 'http://%s/' % self.tenant.primary_domain

        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(response["Location"], response_url)

    @override_settings(ALLOWED_HOSTS="['*']")
    def test_www_domain_redirect(self):

        response = self.client.get('/', HTTP_HOST='www.%s' % self.tenant.primary_domain)

        response_url = 'http://%s/' % self.tenant.primary_domain

        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(response["Location"], response_url)