from mozilla_django_oidc.auth import OIDCAuthenticationBackend

import reversion

from .models import User

class OIDCAuthBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        sub = claims.get('sub')

        if not sub:
            return User.objects.none()

        return User.objects.filter(external_id__iexact=sub)

    def create_user(self, claims):
        return User.objects.create_user(
            name=claims.get('name'),
            email=claims.get('email'),
            picture=claims.get('picture'),
            password=None,
            external_id=claims.get('sub')
        )

    def update_user(self, user, claims):
        with reversion.create_revision():
            user.name = claims.get('name')
            user.email = claims.get('email')
            user.picture = claims.get('picture')
            user.save()

            reversion.set_comment("OIDC Update")

        return user
