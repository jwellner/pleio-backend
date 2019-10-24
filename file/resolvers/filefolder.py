from ariadne import ObjectType
from django.utils.text import slugify
from core.resolvers import shared

filefolder = ObjectType("FileFolder")

@filefolder.field("subtype")
def resolve_subtype(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string()

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

    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )
    if obj.is_folder:
        return '{}/files/view/{}'.format(
            prefix, obj.guid
        ).lower()

    return '{}/files/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()


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
