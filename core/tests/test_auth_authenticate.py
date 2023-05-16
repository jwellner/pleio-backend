from unittest import mock
import uuid

from django.core.exceptions import SuspiciousOperation
from django.test import override_settings, tag
from django.utils.crypto import get_random_string

from core import config
from core.tests.helpers_oidc import BaseOIDCAuthBackendTestCase
from user.factories import UserFactory


@tag("OIDCAuthBackend")
class TestAuthAuthenticateTestCase(BaseOIDCAuthBackendTestCase):
    ACCOUNT_API_URL = "https://account.pleio.local"
    ORIGIN_TOKEN = None

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.ORIGIN_TOKEN = uuid.uuid4()

    def test_without_request_param(self):
        self.assertEqual(None, self.backend.authenticate(None))

    @override_settings(ENV='test')
    @override_settings(ACCOUNT_SYNC_ENABLED=True)
    @override_settings(ACCOUNT_API_URL=ACCOUNT_API_URL)
    @mock.patch("uuid.uuid4")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_or_create_user")
    @mock.patch("core.auth.absolutify")
    def test_with_sync_enabled(self, mocked_absolutify, mocked_get_user, mocked_verify_token, mocked_get_token, mocked_uuid4):
        mocked_get_token.return_value = {
            'id_token': get_random_string(),
            'access_token': get_random_string(),
        }
        mocked_verify_token.return_value = True
        mocked_get_user.return_value = self.authenticated_user
        mocked_uuid4.return_value = self.ORIGIN_TOKEN
        mocked_absolutify.return_value = mock.MagicMock()

        result = self.backend.authenticate(self.request)

        self.assertEqual(result, self.authenticated_user)
        self.assertDictEqual(mocked_get_token.call_args.args[0], {
            "client_id": self.backend.OIDC_RP_CLIENT_ID,
            "client_secret": self.backend.OIDC_RP_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": self.request.GET['code'],
            "redirect_uri": mocked_absolutify.return_value,
            "origin_url": "https://%s" % self.tenant.primary_domain,
            "origin_name": config.NAME,
            "origin_description": config.DESCRIPTION,
            "origin_api_token": config.TENANT_API_TOKEN,
            "origin_token": self.ORIGIN_TOKEN,
        })

    @override_settings(ENV='test')
    @override_settings(ACCOUNT_SYNC_ENABLED=False)
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_or_create_user")
    @mock.patch("core.auth.absolutify")
    def test_without_sync_enabled(self, mocked_absolutify, mocked_get_user, mocked_verify_token, mocked_get_token):
        mocked_get_token.return_value = {
            'id_token': get_random_string(),
            'access_token': get_random_string(),
        }
        mocked_verify_token.return_value = True
        mocked_get_user.return_value = self.authenticated_user
        mocked_absolutify.return_value = mock.MagicMock()

        result = self.backend.authenticate(self.request)

        self.assertEqual(result, self.authenticated_user)
        self.assertDictEqual(mocked_get_token.call_args.args[0], {
            "client_id": self.backend.OIDC_RP_CLIENT_ID,
            "client_secret": self.backend.OIDC_RP_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": self.request.GET['code'],
            "redirect_uri": mocked_absolutify.return_value,
        })

    @override_settings(ACCOUNT_SYNC_ENABLED=False)
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token")
    @mock.patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_or_create_user")
    def test_with_suspicious_operation(self, mocked_get_user, mocked_verify_token, mocked_get_token):
        mocked_get_token.return_value = {
            'id_token': get_random_string(),
            'access_token': get_random_string(),
        }
        mocked_verify_token.return_value = True
        mocked_get_user.return_value = self.authenticated_user
        mocked_get_user.side_effect = SuspiciousOperation()

        result = self.backend.authenticate(self.request)

        self.assertTrue(mocked_get_user.called)
        self.assertEqual(result, None)
