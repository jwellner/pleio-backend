from unittest import mock

import faker
from django.test import tag
from django.utils.crypto import get_random_string

from core import override_local_config
from core.auth import RequestAccessInvalidCodeException, RequestAccessException, OnboardingException
from core.models import SiteInvitation
from core.tests.helpers_oidc import BaseOIDCAuthBackendTestCase


@tag("OIDCAuthBackend")
class TestAuthUserCreateTestCase(BaseOIDCAuthBackendTestCase):

    def setUp(self):
        # Given.
        super().setUp()

        self.backend.request = self.request
        self.claims = {
            'name': faker.Faker().name(),
            'email': faker.Faker().email(),
        }

    @mock.patch("user.models.Manager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_create_user(self, mocked_requires_approval, mocked_create_user):
        mocked_requires_approval.return_value = False
        mocked_create_user.return_value = mock.MagicMock()

        # When.
        result = self.backend.create_user(self.claims)

        # Then.
        self.assertEqual(result, mocked_create_user.return_value)
        self.assertTrue(mocked_create_user.called)
        self.assertDictEqual(mocked_create_user.call_args.kwargs, {
            'name': self.claims['name'],
            'email': self.claims['email'],
            'picture': None,
            'is_government': None,
            'has_2fa_enabled': None,
            'password': None,
            'external_id': None,
            'is_superadmin': False,
        })

    @mock.patch("user.models.Manager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_without_approval_with_code(self, mocked_requires_approval, mocked_create_user):
        mocked_requires_approval.return_value = False
        mocked_create_user.return_value = mock.MagicMock()
        self.request.session['invitecode'] = get_random_string()

        # When.
        result = self.backend.create_user(self.claims)

        self.assertEqual(result, mocked_create_user.return_value)
        self.assertTrue(mocked_create_user.called)
        self.assertDictEqual(mocked_create_user.call_args.kwargs, {
            'name': self.claims['name'],
            'email': self.claims['email'],
            'picture': None,
            'is_government': None,
            'has_2fa_enabled': None,
            'password': None,
            'external_id': None,
            'is_superadmin': False,
        })

    @mock.patch("user.models.Manager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_with_approval(self, mocked_create_user, mocked_requires_approval):
        mocked_requires_approval.return_value = True
        invitation = SiteInvitation.objects.create(code=get_random_string())
        self.request.session['invitecode'] = invitation.code

        self.backend.create_user(self.claims)
        self.assertFalse(SiteInvitation.objects.filter(id=invitation.id).exists())
        self.assertTrue(mocked_create_user.called)

    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_with_nonexistent_invitecode(self, mocked_requires_approval):
        mocked_requires_approval.return_value = True
        self.request.session['invitecode'] = get_random_string()

        with self.assertRaises(RequestAccessInvalidCodeException):
            self.backend.create_user(self.claims)

    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_without_invitecode(self, mocked_requires_approval):
        mocked_requires_approval.return_value = True

        with self.assertRaises(RequestAccessException):
            self.backend.create_user(self.claims)

        self.assertDictEqual(self.request.session['request_access_claims'], self.claims)

    @override_local_config(ONBOARDING_ENABLED=True)
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_with_onboarding(self, mocked_requires_approval):
        mocked_requires_approval.return_value = False

        with self.assertRaises(OnboardingException):
            self.backend.create_user(self.claims)

        self.assertDictEqual(self.request.session['onboarding_claims'], self.claims)
