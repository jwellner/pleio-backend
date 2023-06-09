from ariadne import ObjectType
from core.resolvers import shared

wiki = ObjectType("Wiki")


@wiki.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string


@wiki.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()


@wiki.field("children")
def resolve_children(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.children.visible(info.context["request"].user)
    except AttributeError:
        return []


@wiki.field("parent")
def resolve_parent(obj, info):
    # pylint: disable=unused-argument
    return obj.parent


@wiki.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None


@wiki.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group


@wiki.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


@wiki.field("isFeatured")
def resolve_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured


wiki.set_field("guid", shared.resolve_entity_guid)
wiki.set_field("status", shared.resolve_entity_status)
wiki.set_field("title", shared.resolve_entity_title)
wiki.set_field("abstract", shared.resolve_entity_abstract)
wiki.set_field("description", shared.resolve_entity_description)
wiki.set_field("richDescription", shared.resolve_entity_rich_description)
wiki.set_field("excerpt", shared.resolve_entity_excerpt)
wiki.set_field("tags", shared.resolve_entity_tags)
wiki.set_field("tagCategories", shared.resolve_entity_categories)
wiki.set_field("timeCreated", shared.resolve_entity_time_created)
wiki.set_field("timeUpdated", shared.resolve_entity_time_updated)
wiki.set_field("timePublished", shared.resolve_entity_time_published)
wiki.set_field("scheduleArchiveEntity", shared.resolve_entity_schedule_archive_entity)
wiki.set_field("scheduleDeleteEntity", shared.resolve_entity_schedule_delete_entity)
wiki.set_field("statusPublished", shared.resolve_entity_status_published)
wiki.set_field("canEdit", shared.resolve_entity_can_edit)
wiki.set_field("canBookmark", shared.resolve_entity_can_bookmark)
wiki.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
wiki.set_field("accessId", shared.resolve_entity_access_id)
wiki.set_field("writeAccessId", shared.resolve_entity_write_access_id)
wiki.set_field("owner", shared.resolve_entity_owner)
wiki.set_field("isPinned", shared.resolve_entity_is_pinned)
wiki.set_field("featured", shared.resolve_entity_featured)
wiki.set_field("lastSeen", shared.resolve_entity_last_seen)
wiki.set_field("suggestedItems", shared.resolve_entity_suggested_items)
