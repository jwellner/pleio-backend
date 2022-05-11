import uuid

from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView, OIDCAuthenticationRequestView
from mozilla_django_oidc.utils import absolutify
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.http import urlencode

from core import config
from core.constances import OIDC_PROVIDER_OPTIONS
from core.models import SiteInvitation, SiteAccessRequest

import logging

from user.models import User

LOGGER = logging.getLogger(__name__)


class RequestAccessException(Exception):
    pass


class RequestAccessInvalidCodeException(RequestAccessException):
    pass


class OnboardingException(Exception):
    pass


class OIDCAuthCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request):

        # TODO: catch RequestAccessInvalidCodeException ?

        try:
            return super(OIDCAuthCallbackView, self).get(request)
        except RequestAccessException:
            return redirect(reverse('request_access'))
        except OnboardingException:
            return redirect(reverse('onboarding'))


class OIDCAuthenticateView(OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        idp = self.request.GET.get('idp')
        extra_params = self.get_settings('OIDC_AUTH_REQUEST_EXTRA_PARAMS', {})
        if idp:
            extra_params.update({'idp': idp})

        provider = self.request.GET.get('provider', None)
        providerOption = next(filter(lambda option: option['value'] == provider, OIDC_PROVIDER_OPTIONS), None)
        if providerOption and not providerOption.get('isDefault', False):
            extra_params.update({'provider': provider})

        return extra_params


class OIDCAuthBackend(OIDCAuthenticationBackend):

    def filter_users_by_claims(self, claims):
        external_id = claims.get('sub')
        email = claims.get('email')

        if not external_id or not email:
            return User.objects.none()

        return User.objects.filter(Q(external_id__iexact=external_id) | Q(email__iexact=email))

    def create_user(self, claims):
        if self.requires_approval(claims):
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
        else:
            if self.request.session.get('invitecode'):
                SiteInvitation.objects.filter(code=self.request.session.get('invitecode')).delete()
            else:
                SiteInvitation.objects.filter(email=claims.get('email')).delete()

        # create user should be done after onboarding
        if config.ONBOARDING_ENABLED:
            self.request.session['onboarding_claims'] = claims
            raise OnboardingException

        user = User.objects.create_user(
            name=claims.get('name'),
            email=claims.get('email'),
            picture=claims.get('picture', None),
            is_government=claims.get('is_government'),
            has_2fa_enabled=claims.get('has_2fa_enabled'),
            password=None,
            external_id=claims.get('sub'),
            is_superadmin=claims.get('is_admin', False)
        )

        return user

    def requires_approval(self, claims):
        """Check whether a new user needs approval of an admin before they can be given access based on their claims and the site's configuration"""

        return (
                not config.ALLOW_REGISTRATION  # a site that allows registration, automatically accepts new users
                and not claims.get('is_admin', False)  # Pleio admins (not site admins) do not need approval
                and not claims.get('email').split('@')[
                            1] in config.DIRECT_REGISTRATION_DOMAINS  # Approval can be skipped for configured email domains
                and not SiteAccessRequest.objects.filter(email=claims.get('email'),
                                                         accepted=True).first()  # Users that are already approved, don't require it
                and not self.approve_by_sso(claims)  # Users can be approved based on the SSO they use
        )

    def approve_by_sso(self, claims):
        """Check if a user can be approved based on the sso they use (i.e. is one of the configured saml/oidc providers)"""
        if not config.AUTO_APPROVE_SSO:
            return False

        return (
                set(claims.get('sso', [])) & set(config.OIDC_PROVIDERS)
                or set(claims.get('sso', [])) & set([config.IDP_ID])
        )

    def update_user(self, user, claims):
        SiteInvitation.objects.filter(email=claims.get('email')).delete()

        user.external_id = claims.get('sub')

        if not config.EDIT_USER_NAME_ENABLED:
            user.name = claims.get('name')

        user.email = claims.get('email')

        # if user profile picture file exists, do not change to picture from account
        if claims.get('picture'):
            user.picture = claims.get('picture')
        else:
            user.picture = None

        user.is_government = claims.get('is_government')
        user.has_2fa_enabled = claims.get('has_2fa_enabled')

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


        if settings.ACCOUNT_SYNC_ENABLED and settings.ACCOUNT_API_URL:
            # Fresh origin token.
            origin_token = uuid.uuid4()

            url_schema = "http" if settings.ENV == 'local' else "https"
            url_port = ":8000" if settings.ENV == 'local' else ""

            token_payload['origin_name'] = request.tenant.name
            token_payload['origin_url'] = "{}://{}{}".format(url_schema, request.tenant.primary_domain, url_port)
            token_payload['origin_token'] = origin_token
        else:
            origin_token = None

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

                if origin_token:
                    user.profile.update_origin_token(origin_token)

                return user
            except SuspiciousOperation as e:
                LOGGER.warning('failed to get or create user: %s', e)
                return None

        return None


def oidc_provider_logout_url(request):
    return_url = request.build_absolute_uri('/')
    query_params = urlencode({'post_logout_redirect_uri': return_url})
    return f"{settings.OIDC_OP_LOGOUT_ENDPOINT}?{query_params}"
