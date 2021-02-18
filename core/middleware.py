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

from django.template.response import TemplateResponse

from core import config
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
        translation.activate(config.LANGUAGE)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        language = translation.get_language()
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
        public_urls += (r"^{}.+$".format("/file/featured"),)
        public_urls += ("/login",)
        public_urls += ("/login/request",)
        public_urls += ("/logout",)
        public_urls += ("/onboarding",)
        public_urls += ("/robots.txt",)
        public_urls += ("/sitemap.xml",)
        public_urls = [re.compile(v) for v in public_urls]

        return any(public_url.match(url) for public_url in public_urls)

    def __call__(self, request):
        if (
            config.IS_CLOSED
            and not request.user.is_authenticated
            and not self.is_public_url(request.path_info)
        ) or (
            config.WALLED_GARDEN_BY_IP_ENABLED
            and not is_ip_whitelisted(request)
        ):
            context = {
                'next': request.path_info
            }

            return TemplateResponse(request, 'registration/login.html', context).render()

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
        public_urls += (r"^{}.+$".format("/file/featured"),)
        public_urls += ("/login",)
        public_urls += ("/robots.txt",)
        public_urls += ("/sitemap.xml",)
        public_urls += ("/onboarding",)
        public_urls += ("/admin2",)
        public_urls += ("/graphql",)
        public_urls = [re.compile(v) for v in public_urls]

        return any(public_url.match(url) for public_url in public_urls)

    def __call__(self, request):

        user = request.user
        if (
            not self.is_public_url(request.path_info)
            and user.is_authenticated
            and config.ONBOARDING_ENABLED
            and config.ONBOARDING_FORCE_EXISTING_USERS
            and not user.is_profile_complete
        ):
            return redirect('onboarding')

        return self.get_response(request)


class RedirectMiddleware:
    """
    Show onboarding when user has to complete mandatory fields

    Note: new user onboaring is routed in authentication layer
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ignore graphql first (more efficiency for all graphql queries)
        if not request.path == '/graphql' and request.path in config.REDIRECTS and resolve(request.path).url_name in ["entity_view", "default"]:
            return redirect(config.REDIRECTS[request.path])

        return response
