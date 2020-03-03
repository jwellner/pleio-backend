from ariadne import ObjectType
from core.resolvers import shared

filefolder = ObjectType("FileFolder")

@filefolder.field("subtype")
def resolve_subtype(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string

@filefolder.field("parentFolder")
def resolve_parent_folder(obj, info):
    # pylint: disable=unused-argument
    return obj.parent

@filefolder.field("mimeType")
def resolve_mimetype(obj, info):
    # pylint: disable=unused-argument
    return obj.mime_type

@filefolder.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()

@filefolder.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@filefolder.field("thumbnail")
def resolve_thumbnail(obj, info):
    # pylint: disable=unused-argument
    mime_types = [
                    'image/jpeg',
                    'image/pjpeg',
                    'image/png',
                    'image/x-png',
                    'image/gif'
                 ]
    # Only thumbnails for images
    if obj.mime_type not in mime_types:
        return None

    return obj.thumbnail_url

@filefolder.field("download")
def resolve_download(obj, info):
    # pylint: disable=unused-argument

    if obj.is_folder:
        return None

    return obj.download


filefolder.set_field("guid", shared.resolve_entity_guid)
filefolder.set_field("status", shared.resolve_entity_status)
filefolder.set_field("title", shared.resolve_entity_title)
filefolder.set_field("tags", shared.resolve_entity_tags)
filefolder.set_field("timeCreated", shared.resolve_entity_time_created)
filefolder.set_field("timeUpdated", shared.resolve_entity_time_updated)
filefolder.set_field("canEdit", shared.resolve_entity_can_edit)
filefolder.set_field("accessId", shared.resolve_entity_access_id)
filefolder.set_field("writeAccessId", shared.resolve_entity_write_access_id)
filefolder.set_field("views", shared.resolve_entity_views)
filefolder.set_field("owner", shared.resolve_entity_owner)
