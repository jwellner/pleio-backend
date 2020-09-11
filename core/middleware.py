import re
from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path
from django.utils import timezone, translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from django.template.response import TemplateResponse

from core import config


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
        public_urls += ("/robots.txt",)
        public_urls += ("/sitemap.xml",)
        public_urls = [re.compile(v) for v in public_urls]

        return any(public_url.match(url) for public_url in public_urls)

    def __call__(self, request):
        if (
            config.IS_CLOSED
            and not request.user.is_authenticated
            and not self.is_public_url(request.path_info)
        ):
            context = {
                'next': request.path_info
            }

            return TemplateResponse(request, 'registration/login.html', context).render()

        return self.get_response(request)
