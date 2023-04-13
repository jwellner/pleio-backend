import logging
from ariadne import ObjectType

logger = logging.getLogger(__name__)

attachment = ObjectType("Attachment")


@attachment.field('id')
def resolve_id(obj, info):
    # pylint: disable=unused-argument
    return obj.guid


@attachment.field('url')
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.attachment_url


@attachment.field('mimeType')
def resolve_mime_type(obj, info):
    # pylint: disable=unused-argument
    return obj.mime_type


@attachment.field('name')
def resolve_name(obj, info):
    # pylint: disable=unused-argument
    return obj.title
