import logging
import os
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import module_dir, import_string
from django.utils.translation import gettext as _

from external_content.models import ExternalContentSource

logger = logging.getLogger(__name__)


# Deze is werkloos nu.
def get_external_content_sources():
    return [{
        "key": source.guid,
        "value": source.name,
    } for source in ExternalContentSource.objects.all()]


def get_external_content_subtypes():
    return [str(pk) for pk in ExternalContentSource.objects.all().values_list('id', flat=True)]


def is_external_content_source(subtype):
    return subtype in get_external_content_subtypes()


def find_handlers():
    for app in apps.get_app_configs():
        yield from _find_handlers_recursive("%s.api_handlers" % app.name)


def _find_handlers_recursive(module_name):
    try:
        yield from _maybe_module_contains_handler(module_name)
        result = import_module(module_name)
        for file in os.scandir(module_dir(result)):
            if file.name.startswith('__'):
                continue
            if file.is_dir():
                yield from _find_handlers_recursive("%s.%s" % (module_name, file.name))
            elif file.name.endswith('.py'):
                submodule, ext = os.path.splitext(file.name)
                yield from _maybe_module_contains_handler("%s.%s" % (module_name, submodule))
    except ModuleNotFoundError:
        pass


def _maybe_module_contains_handler(module_name):
    try:
        from external_content.api_handlers import ApiHandlerBase
        handler = import_string("%s.ApiHandler" % module_name)
        assert ApiHandlerBase in handler.__bases__
        yield handler.ID, handler
    except (ModuleNotFoundError, ImportError, AssertionError):
        pass


def get_or_create_default_author():
    from user.models import User
    default_author, created = User.objects.get_or_create(
        email=settings.EXTERNAL_CONTENT_AUTHOR_EMAIL,
    )
    if created:
        default_author.name = _("External content author")
        default_author.is_active = False
        default_author.save()
    return default_author
