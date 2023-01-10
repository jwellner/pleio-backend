from ariadne import ObjectType

from core.resolvers import shared

external_content = ObjectType('ExternalContent')

external_content.set_field("guid", shared.resolve_entity_guid)
external_content.set_field("status", shared.resolve_entity_status)
external_content.set_field("title", shared.resolve_entity_title)
external_content.set_field("timeCreated", shared.resolve_entity_time_created)
external_content.set_field("timeUpdated", shared.resolve_entity_time_updated)
external_content.set_field("timePublished", shared.resolve_entity_time_published)
external_content.set_field("canEdit", shared.resolve_entity_can_edit)
external_content.set_field("accessId", shared.resolve_entity_access_id)
external_content.set_field("writeAccessId", shared.resolve_entity_write_access_id)
external_content.set_field("owner", shared.resolve_entity_owner)
external_content.set_field("tags", shared.resolve_entity_tags)
external_content.set_field("tagCategories", shared.resolve_entity_categories)


@external_content.field("description")
def resolve_description(obj, info):
    # pylint: disable=unused-argument
    return obj.description


@external_content.field("timeCreated")
def resolve_time_created(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at


@external_content.field("timeUpdated")
def resolve_time_updated(obj, info):
    # pylint: disable=unused-argument
    return obj.updated_at


@external_content.field("remoteId")
def resolve_remote_id(obj, info):
    # pylint: disable=unused-argument
    return obj.remote_id


@external_content.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.canonical_url
