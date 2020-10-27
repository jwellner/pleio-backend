from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from mozilla_django_oidc.utils import absolutify
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from core import config
from core.models import SiteInvitation

import logging

from user.models import User

LOGGER = logging.getLogger(__name__)

class RequestAccessException(Exception):
    pass

class RequestAccessInvalidCodeException(RequestAccessException):
    pass

class OIDCAuthCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request):

        # TODO: catch RequestAccessInvalidCodeException ?

        try:
            return super(OIDCAuthCallbackView, self).get(request)
        except RequestAccessException:
            return redirect(reverse('request_access'))

class OIDCAuthBackend(OIDCAuthenticationBackend):
    # TODO: is there a more upgrade friendly way for overriding methods?
    def filter_users_by_claims(self, claims):
        sub = claims.get('sub')

        if not sub:
            return User.objects.none()

        return User.objects.filter(external_id__iexact=sub)

    def create_user(self, claims):

        if not config.ALLOW_REGISTRATION and not claims.get('is_admin', False):

            if self.request.session.get('invitecode'):
                try:
                    invite = SiteInvitation.objects.get(
                        code=self.request.session.get('invitecode')
                    )
                    invite.delete()
                    del self.request.session['invitecode']

                    # Als delete accessRequests if they exist for this user.
                except ObjectDoesNotExist:
                    raise RequestAccessInvalidCodeException
            else:
                # store claims in sessions
                self.request.session['request_access_claims'] = claims
                raise RequestAccessException

        user = User.objects.create_user(
            name=claims.get('name'),
            email=claims.get('email'),
            picture=claims.get('picture', None),
            is_government=claims.get('is_government'),
            has_2fa_enabled=claims.get('has_2fa_enabled'),
            password=None,
            external_id=claims.get('sub')
        )

        if claims.get('is_admin'):
            user.is_superadmin = True
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
        user.login_count = user.login_count + 1 if user.login_count else 1

        # Get and set superadmin
        if claims.get('is_admin'):
            user.is_superadmin = True
        else:
            user.is_superadmin = False

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
            except SuspiciousOperation as e:
                LOGGER.warning('failed to get or create user: %s', e)
                return None

        return None

def oidc_provider_logout(request):
    return settings.OIDC_OP_LOGOUT_ENDPOINT
