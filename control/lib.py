import urllib.parse

from django.conf import settings
from django.shortcuts import reverse as django_reverse
from django_tenants.utils import schema_context


def get_full_url(path):
    if settings.DEBUG:
        return urllib.parse.urljoin(f"http://localhost:8888", path)
    return urllib.parse.urljoin(f"https://{settings.CONTROL_PRIMARY_DOMAIN}", path)


def reverse(*args, **kwargs):
    return django_reverse(*args, urlconf="control.urls", **kwargs)


def schema_config(schema_name, key):
    from core import config
    with schema_context(schema_name):
        return getattr(config, key)
