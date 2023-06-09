import ipaddress
import re
from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path, resolve
from django.utils import timezone, translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib.auth import logout

from django.template.response import TemplateResponse

from core import config
from core.constances import OIDC_PROVIDER_OPTIONS
from core.lib import get_client_ip


def is_ip_whitelisted(request):
    if config.WHITELISTED_IP_RANGES:
        try:
            ip_address_network = ipaddress.ip_network(get_client_ip(request))
            for ip_range in config.WHITELISTED_IP_RANGES:
                try:
                    if ip_address_network.subnet_of(ipaddress.ip_network(ip_range)):
                        return True
                except Exception:
                    pass
        except Exception:
            pass
    return False


class UserLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user
        if not user.is_authenticated:
            return response

        if not user.is_active:
            logout(request)
            return response

        ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)

        try:
            if user.profile.last_online and user.profile.last_online > ten_minutes_ago:
                return response

            user.profile.last_online = timezone.now()
            user.profile.save()
        except Exception:
            pass

        return response


class CustomLocaleMiddleware(MiddlewareMixin):
    """
    Use language defined in config.LANGUAGE, a simplified version of django.middleware.locale.LocaleMiddleware
    """
    response_redirect_class = HttpResponseRedirect

    def process_request(self, request):
        if not settings.RUN_AS_ADMIN_APP:
            if request.user.is_authenticated:
                translation.activate(request.user.get_language())
            else:
                translation.activate(config.LANGUAGE)

    def process_response(self, request, response):
        request.LANGUAGE_CODE = translation.get_language()
        language = request.LANGUAGE_CODE
        language_from_path = translation.get_language_from_path(request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(urlconf)

        if (response.status_code == 404 and not language_from_path and
                i18n_patterns_used and prefixed_default_language):
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            language_path = '/%s%s' % (language, request.path_info)
            path_valid = is_valid_path(language_path, urlconf)
            path_needs_slash = (
                    not path_valid and (
                    settings.APPEND_SLASH and not language_path.endswith('/') and
                    is_valid_path('%s/' % language_path, urlconf)
            )
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = request.get_full_path(force_append_slash=path_needs_slash).replace(
                    script_prefix,
                    '%s%s/' % (script_prefix, language),
                    1
                )
                return self.response_redirect_class(language_url)

        if not (i18n_patterns_used and language_from_path):
            patch_vary_headers(response, ('Accept-Language',))
        response.setdefault('Content-Language', language)
        return response


class WalledGardenMiddleware:
    """
    Site can be closed for not logged in users, if config.IS_CLOSED is True,
    requests will be redirected to a static login page
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def is_public_url(self, url):
        public_urls = ()
        public_urls += (r"^{}.+$".format('/static'),)
        public_urls += (r"^{}.+$".format("/oidc"),)
        public_urls += (r"^{}.+$".format("/profile_sync_api"),)
        public_urls += (r"^{}.+$".format("/flow"),)
        public_urls += (r"^{}.+$".format("/edit_email_settings"),)
        public_urls += (r"^{}.+$".format("/file/featured"),)
        public_urls += (r"^/api/.+$",)
        public_urls += (r"^/unsubscribe/.+$",)
        public_urls += ("/register",)
        public_urls += ("/login",)
        public_urls += ("/login/request",)
        public_urls += ("/logout",)
        public_urls += ("/onboarding",)
        public_urls += ("/unsupported_browser",)
        public_urls += ("/robots.txt",)
        public_urls += ("/sitemap.xml",)
        public_urls += ("/custom.css",)
        public_urls += ("/favicon.png",)
        public_urls = [re.compile(v) for v in public_urls]

        return any(public_url.match(url) for public_url in public_urls)

    def __call__(self, request):

        if request.user.is_authenticated or self.is_public_url(request.path_info):
            pass
        elif (
                config.IS_CLOSED
        ) or (
                config.WALLED_GARDEN_BY_IP_ENABLED
                and not is_ip_whitelisted(request)
        ):
            context = {
                'next': request.path_info,
                'banned': request.session.get('pleio_user_is_banned', False),
                'constants': {
                    'OIDC_PROVIDER_OPTIONS': OIDC_PROVIDER_OPTIONS,
                },
            }

            return TemplateResponse(request, 'registration/login.html', context, status=401).render()

        return self.get_response(request)


class OnboardingMiddleware:
    """
    Show onboarding when user has to complete mandatory fields

    Note: new user onboaring is routed in authentication layer
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def is_public_url(self, url):
        public_urls = ()
        public_urls += (r"^{}.+$".format('/static'),)
        public_urls += (r"^{}.+$".format("/oidc"),)
        public_urls += (r"^{}.+$".format("/profile_sync_api"),)
        public_urls += (r"^{}.+$".format("/flow"),)
        public_urls += (r"^{}.+$".format("/edit_email_settings"),)
        public_urls += (r"^{}.+$".format("/file/featured"),)
        public_urls += (r"^/api/.+$",)
        public_urls += (r"^/unsubscribe/.+$",)
        public_urls += ("/register",)
        public_urls += ("/login",)
        public_urls += ("/robots.txt",)
        public_urls += ("/sitemap.xml",)
        public_urls += ("/onboarding",)
        public_urls += ("/unsupported_browser",)
        public_urls += ("/admin",)
        public_urls += ("/graphql",)
        public_urls = [re.compile(v) for v in public_urls]

        return any(public_url.match(url) for public_url in public_urls)

    def __call__(self, request):
        user = request.user
        if self.restricted_url(request) and self.user_requires_onboarding(user) and self.onboarding_enabled():
            return redirect('onboarding')
        return self.get_response(request)

    def restricted_url(self, request):
        return not self.is_public_url(request.path_info)

    @staticmethod
    def user_requires_onboarding(user):
        return user.is_authenticated and not user.is_superadmin and not user.is_profile_complete

    @staticmethod
    def onboarding_enabled():
        return config.ONBOARDING_ENABLED and config.ONBOARDING_FORCE_EXISTING_USERS


class RedirectMiddleware:
    """
    Custom redirects configured by site admins
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ignore graphql first (more efficiency for all graphql queries)
        if (
                not request.path == '/graphql'
                and request.path in config.REDIRECTS
                and resolve(request.path).url_name in ["entity_view", "default", "redirect_friendly_url"]
        ):
            return redirect(config.REDIRECTS[request.path])

        return response


class TenantPrimaryDomainRedirectMiddleware:
    """
    If current domain is not primary domain redirect to primary domain
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request, 'tenant'):
            current_domain = request.get_host().split(':')[0]
            primary_domain = request.tenant.primary_domain

            if current_domain != primary_domain:
                server_port = request.get_port()
                if server_port != ('443' if request.is_secure() else '80'):
                    primary_domain = '%s:%s' % (primary_domain, server_port)

                redirect_url = f"%s://%s%s" % (request.scheme, primary_domain, request.get_full_path())
                return redirect(redirect_url, permanent=True)

        return response


class UnsupportedBrowserMiddleware:
    """
    Detect unsupported browser and redirect to information page
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # unsupported browser detection
        if (
                request.META.get('HTTP_USER_AGENT', '').find('Trident') != -1
                and resolve(request.path).url_name in ["entity_view", "default", "onboarding"]
        ):
            return redirect('/unsupported_browser')

        return response


class CustomCSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        scheme = 'wss' if request.is_secure() else 'ws'
        response._csp_update = {'connect-src': "%s://%s" % (scheme, request.get_host())}

        if config.CSP_HEADER_EXCEPTIONS:
            response._csp_update = {'img-src': config.CSP_HEADER_EXCEPTIONS, 'frame-src': config.CSP_HEADER_EXCEPTIONS}

        return response


class AcrCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
                config.REQUIRE_2FA
                and request.user.is_authenticated
                and not request.user.has_2fa_enabled
        ):
            logout(request)

            context = {
                'endpoint_2fa': settings.ENDPOINT_2FA,
            }
            return TemplateResponse(request, 'registration/2fa_required.html', context, status=403).render()

        return self.get_response(request)


class AnonymousVisitorSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session or not request.session.session_key:
            request.session.save()
        return self.get_response(request)
