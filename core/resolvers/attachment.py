import logging
from ariadne import ObjectType

logger = logging.getLogger(__name__)

attachment = ObjectType("Attachment")

@attachment.field('id')
def resolve_id(obj, info):
    # pylint: disable=unused-argument
    return obj.id

@attachment.field('url')
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@attachment.field('mimeType')
def resolve_mime_type(obj, info):
    # pylint: disable=unused-argument
    return obj.mime_type

@attachment.field('name')
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.name
