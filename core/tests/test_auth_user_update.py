from django.test import tag

from core import override_local_config
from core.tests.helpers_oidc import BaseOIDCAuthBackendTestCase
from user.factories import UserFactory


@tag("OIDCAuthBackend")
class TestAuthUserUpdateTestCase(BaseOIDCAuthBackendTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory(
            external_id=1,
            name="Original name",
            email="original@mail.net",
            picture="https://pictureplanet.net/original.jpg",
            is_government=False,
            has_2fa_enabled=False,
            is_superadmin=False,
        )
        self.backend.request = self.request
        self.claims = {
            'sub': "77421",
            'name': "Updated name",
            'email': "updated@mail.net",
            'picture': "https://pictureplanet.net/updated.jpg",
            'is_government': True,
            'has_2fa_enabled': True,
            'is_admin': True,
        }

    @staticmethod
    def serialize_user(user):
        return {
            "external_id": user.external_id,
            "name": user.name,
            "email": user.email,
            "picture": user.picture,
            "is_government": user.is_government,
            "has_2fa_enabled": user.has_2fa_enabled,
            "is_superadmin": user.is_superadmin,
        }

    def applyClaims(self):
        # Given.
        before = self.serialize_user(self.user)

        # When.
        self.backend.update_user(self.user, self.claims)
        self.user.refresh_from_db()

        return before, self.serialize_user(self.user)

    def test_user_update(self):
        # Given. When.
        before, after = self.applyClaims()

        # Then.
        self.assertNotEqual(after['external_id'], before['external_id'])
        self.assertEqual(after['external_id'], self.claims['sub'])

        self.assertNotEqual(after['name'], before['name'])
        self.assertEqual(after['name'], self.claims['name'])

        self.assertNotEqual(after['email'], before['email'])
        self.assertEqual(after['email'], self.claims['email'])

        self.assertNotEqual(after['picture'], before['picture'])
        self.assertEqual(after['picture'], self.claims['picture'])

        self.assertNotEqual(after['is_government'], before['is_government'])
        self.assertEqual(after['is_government'], self.claims['is_government'])

        self.assertNotEqual(after['has_2fa_enabled'], before['has_2fa_enabled'])
        self.assertEqual(after['has_2fa_enabled'], self.claims['has_2fa_enabled'])

        self.assertNotEqual(after['is_superadmin'], before['is_superadmin'])
        self.assertEqual(after['is_superadmin'], self.claims['is_admin'])

    # @notice: This is a counterintuitively named configuration property.
    @override_local_config(EDIT_USER_NAME_ENABLED=True)
    def test_user_update_without_name(self):
        # Given. When.
        before, after = self.applyClaims()

        self.assertEqual(after['name'], before['name'])
        self.assertNotEqual(after['name'], self.claims['name'])

        # Reference value
        self.assertNotEqual(after['external_id'], before['external_id'])
        self.assertEqual(after['external_id'], self.claims['sub'])

    def test_user_update_without_picture(self):
        # Given.
        self.claims.pop("picture", None)

        # When.
        before, after = self.applyClaims()

        # Then.
        self.assertEqual(after['picture'], None)

    def test_user_update_without_admin(self):
        # Given.
        self.claims.pop("is_admin", None)

        # When.
        before, after = self.applyClaims()

        # Then.
        self.assertEqual(after['is_superadmin'], False)
