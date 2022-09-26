from unittest import mock

import faker
from django.test import tag
from django.utils.crypto import get_random_string

from core import override_local_config
from core.auth import RequestAccessInvalidCodeException, RequestAccessException, OnboardingException
from core.models import SiteInvitation
from core.tests.helpers_oidc import BaseOIDCAuthBackendTestCase
from user.models import User


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

    def assertValidHandleCreateUser(self, result, mocked_create_user):
        mocked_user = mocked_create_user.return_value
        self.assertEqual(result, mocked_create_user.return_value)
        self.assertTrue(mocked_create_user.called)
        self.assertDictEqual(mocked_create_user.call_args.kwargs, {
            'email': self.claims['email'],
            'name': self.claims['name'],
        })
        self.assertTrue(mocked_user.apply_claims.called)
        self.assertEqual(mocked_user.apply_claims.call_args.args[0], self.claims)

    @mock.patch("user.models.UserManager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_create_user(self, mocked_requires_approval, mocked_create_user):
        mocked_requires_approval.return_value = False
        mocked_create_user.return_value  = mock.MagicMock(spec=User)

        # When.
        result = self.backend.create_user(self.claims)

        # Then.
        self.assertValidHandleCreateUser(result, mocked_create_user)

    @mock.patch("user.models.UserManager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_without_approval_with_code(self, mocked_requires_approval, mocked_create_user):
        mocked_requires_approval.return_value = False
        mocked_create_user.return_value = mock.MagicMock(spec=User)
        self.request.session['invitecode'] = get_random_string()

        # When.
        result = self.backend.create_user(self.claims)

        # Then.
        self.assertValidHandleCreateUser(result, mocked_create_user)

    @mock.patch("user.models.UserManager.create_user")
    @mock.patch("core.auth.OIDCAuthBackend.requires_approval")
    def test_with_approval(self, mocked_requires_approval, mocked_create_user):
        mocked_requires_approval.return_value = True
        invitation = SiteInvitation.objects.create(code=get_random_string())
        mocked_create_user.return_value = mock.MagicMock(spec=User)
        self.request.session['invitecode'] = invitation.code

        result = self.backend.create_user(self.claims)
        self.assertFalse(SiteInvitation.objects.filter(id=invitation.id).exists())

        self.assertValidHandleCreateUser(result, mocked_create_user)

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
