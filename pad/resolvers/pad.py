from ariadne import ObjectType
from core.resolvers import shared

pad = ObjectType("Pad")

@pad.field("subtype")
def resolve_subtype(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string


@pad.field("parentFolder")
def resolve_parent_folder(obj, info):
    # pylint: disable=unused-argument
    return obj.parent


@pad.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


@pad.field("state")
def resolve_state(obj, info):
    # pylint: disable=unused-argument
    return obj.pad_state


pad.set_field("guid", shared.resolve_entity_guid)
pad.set_field("status", shared.resolve_entity_status)
pad.set_field("title", shared.resolve_entity_title)
pad.set_field("tags", shared.resolve_entity_tags)
pad.set_field("timeCreated", shared.resolve_entity_time_created)
pad.set_field("timeUpdated", shared.resolve_entity_time_updated)
pad.set_field("timePublished", shared.resolve_entity_time_published)
pad.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
pad.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
pad.set_field("canEdit", shared.resolve_entity_can_edit)
pad.set_field("accessId", shared.resolve_entity_access_id)
pad.set_field("writeAccessId", shared.resolve_entity_write_access_id)
pad.set_field("views", shared.resolve_entity_views)
pad.set_field("owner", shared.resolve_entity_owner)
pad.set_field("isPinned", shared.resolve_entity_is_pinned)
pad.set_field("tags", shared.resolve_entity_tags)
pad.set_field("richDescription", shared.resolve_entity_rich_description)
