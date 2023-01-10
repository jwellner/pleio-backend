from mixer.backend.django import mixer

from external_content.api_handlers.default import ApiHandler as DefaultHandler
from external_content.models import ExternalContent, ExternalContentSource
from external_content.utils import get_or_create_default_author


def ExternalContentFactory(**attributes) -> ExternalContent:
    assert attributes.get('source'), "Source is mandatory for ExternalContent entities."
    if 'owner' not in attributes:
        attributes['owner'] = get_or_create_default_author()
    return mixer.blend(ExternalContent, **attributes)


def ExternalContentSourceFactory(**attributes) -> ExternalContentSource:
    attributes.setdefault('handler_id', DefaultHandler.ID)
    return mixer.blend(ExternalContentSource, **attributes)
