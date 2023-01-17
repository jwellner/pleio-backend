from django.http import HttpRequest

from core.lib import validate_token
from core.tests.helpers import PleioTenantTestCase


class TestLibValidateTokenTestCase(PleioTenantTestCase):

    def test_request_without_token(self):
        request = HttpRequest()
        self.assertFalse(validate_token(request, None))
        self.assertFalse(validate_token(request, "expected-token"))

    def test_validate_http_authorization_token(self):
        request = HttpRequest()
        request.META['HTTP_AUTHORIZATION'] = "Bearer expected-token"
        self.assertTrue(validate_token(request, "expected-token"))
        self.assertFalse(validate_token(request, "unexpected-token"))
