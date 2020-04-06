from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import absolutify
from django.urls import reverse
from django.conf import settings

import logging

from user.models import User

LOGGER = logging.getLogger(__name__)


class OIDCAuthBackend(OIDCAuthenticationBackend):
    # TODO: is there a more upgrade friendly way for overriding methods?
    def filter_users_by_claims(self, claims):
        sub = claims.get('sub')

        if not sub:
            return User.objects.none()

        return User.objects.filter(external_id__iexact=sub)

    def create_user(self, claims):

        if claims.get('picture'):
            picture = claims.get('picture')
        else:
            picture = None

        user = User.objects.create_user(
            name=claims.get('name'),
            email=claims.get('email'),
            picture=picture,
            is_government=claims.get('is_government'),
            has_2fa_enabled=claims.get('has_2fa_enabled'),
            password=None,
            external_id=claims.get('sub')
        )

        if claims.get('is_admin'):
            user.is_admin = True
            user.save()

        return user

    def update_user(self, user, claims):

        user.name = claims.get('name')
        user.email = claims.get('email')
        if claims.get('picture'):
            user.picture = claims.get('picture')
        else:
            user.picture = None
        user.is_government = claims.get('is_government')
        user.has_2fa_enabled = claims.get('has_2fa_enabled')
        user.is_admin = claims.get('is_admin')
        user.save()

        return user

    def authenticate(self, request, **kwargs):
        """Authenticates a user based on the OIDC code flow."""
        # pylint: disable=too-many-locals

        self.request = request
        if not self.request:
            return None

        state = self.request.GET.get('state')
        code = self.request.GET.get('code')
        nonce = kwargs.pop('nonce', None)

        if not code or not state:
            return None

        reverse_url = self.get_settings('OIDC_AUTHENTICATION_CALLBACK_URL',
                                        'oidc_authentication_callback')

        token_payload = {
            'client_id': self.OIDC_RP_CLIENT_ID,
            'client_secret': self.OIDC_RP_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': absolutify(
                self.request,
                reverse(reverse_url)
            ),
        }

        # Get the token
        token_info = self.get_token(token_payload)
        id_token = token_info.get('id_token')
        access_token = token_info.get('access_token')

        # Validate the token
        payload = self.verify_token(id_token, nonce=nonce)

        if payload:
            self.store_tokens(access_token, id_token)
            try:
                user = self.get_or_create_user(access_token, id_token, payload)
                is_active = getattr(user, 'is_active', None)
                if not is_active:
                    request.session['pleio_user_is_banned'] = True
                elif 'pleio_user_is_banned' in request.session:
                    del request.session['pleio_user_is_banned']
                return user
            except SuspiciousOperation as exc:
                LOGGER.warning('failed to get or create user: %s', exc)
                return None

        return None

def oidc_provider_logout(request):
    return settings.OIDC_OP_LOGOUT_ENDPOINT