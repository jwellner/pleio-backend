from ariadne import ObjectType, InterfaceType
from core.resolvers import shared

file = ObjectType("File")
folder = ObjectType("Folder")
filefolder = InterfaceType("FileFolder")

@filefolder.type_resolver
def resolve_filefolder_type(obj, *_):
    return obj.type

@file.field("subtype")
@folder.field("subtype")
def resolve_subtype(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string


@file.field("parentFolder")
@folder.field("parentFolder")
def resolve_parent_folder(obj, info):
    # pylint: disable=unused-argument
    return obj.parent


@file.field("mimeType")
def resolve_mimetype(obj, info):
    # pylint: disable=unused-argument
    return obj.mime_type


@file.field("hasChildren")
@folder.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()


@file.field("url")
@folder.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


@file.field("thumbnail")
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


@file.field("download")
def resolve_download(obj, info):
    # pylint: disable=unused-argument
    return obj.download_url


@file.field("size")
def resolve_size(obj, info):
    # pylint: disable=unused-argument
    return obj.size


file.set_field("guid", shared.resolve_entity_guid)
file.set_field("status", shared.resolve_entity_status)
file.set_field("title", shared.resolve_entity_title)
file.set_field("tags", shared.resolve_entity_tags)
file.set_field("timeCreated", shared.resolve_entity_time_created)
file.set_field("timeUpdated", shared.resolve_entity_time_updated)
file.set_field("timePublished", shared.resolve_entity_time_published)
file.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
file.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
file.set_field("canEdit", shared.resolve_entity_can_edit)
file.set_field("accessId", shared.resolve_entity_access_id)
file.set_field("writeAccessId", shared.resolve_entity_write_access_id)
file.set_field("views", shared.resolve_entity_views)
file.set_field("owner", shared.resolve_entity_owner)
file.set_field("isPinned", shared.resolve_entity_is_pinned)
file.set_field("tags", shared.resolve_entity_tags)
file.set_field("richDescription", shared.resolve_entity_rich_description)

folder.set_field("guid", shared.resolve_entity_guid)
folder.set_field("status", shared.resolve_entity_status)
folder.set_field("title", shared.resolve_entity_title)
folder.set_field("tags", shared.resolve_entity_tags)
folder.set_field("timeCreated", shared.resolve_entity_time_created)
folder.set_field("timeUpdated", shared.resolve_entity_time_updated)
folder.set_field("timePublished", shared.resolve_entity_time_published)
folder.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
folder.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
folder.set_field("canEdit", shared.resolve_entity_can_edit)
folder.set_field("accessId", shared.resolve_entity_access_id)
folder.set_field("writeAccessId", shared.resolve_entity_write_access_id)
folder.set_field("views", shared.resolve_entity_views)
folder.set_field("owner", shared.resolve_entity_owner)
folder.set_field("isPinned", shared.resolve_entity_is_pinned)
folder.set_field("tags", shared.resolve_entity_tags)
folder.set_field("richDescription", shared.resolve_entity_rich_description)

