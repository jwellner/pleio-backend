from django.http import HttpRequest
from django.utils.crypto import get_random_string

from core.auth import OIDCAuthBackend
from tenants.helpers import FastTenantTestCase


class BaseOIDCAuthBackendTestCase(FastTenantTestCase):
    backend: OIDCAuthBackend = None
    request: HttpRequest = None

    def setUp(self):
        super().setUp()

        self.backend = OIDCAuthBackend()
        self.request = self.build_request()

    def build_request(self):
        request = HttpRequest()
        request.GET['code'] = get_random_string()
        request.GET['state'] = get_random_string()
        request.META['SERVER_NAME'] = self.tenant.primary_domain
        request.META['SERVER_PORT'] = 8000
        request.session = {}
        return request
