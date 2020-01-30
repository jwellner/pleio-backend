from ariadne import ObjectType
from core.resolvers import shared

wiki = ObjectType("Wiki")

@wiki.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()

@wiki.field("children")
def resolve_children(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.children.all()
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


wiki.set_field("guid", shared.resolve_entity_guid)
wiki.set_field("status", shared.resolve_entity_status)
wiki.set_field("title", shared.resolve_entity_title)
wiki.set_field("description", shared.resolve_entity_description)
wiki.set_field("richDescription", shared.resolve_entity_rich_description)
wiki.set_field("excerpt", shared.resolve_entity_excerpt)
wiki.set_field("tags", shared.resolve_entity_tags)
wiki.set_field("timeCreated", shared.resolve_entity_time_created)
wiki.set_field("timeUpdated", shared.resolve_entity_time_updated)
wiki.set_field("canEdit", shared.resolve_entity_can_edit)
wiki.set_field("canBookmark", shared.resolve_entity_can_bookmark)
wiki.set_field("isBookmarked", shared.resolve_entity_is_bookmarked)
wiki.set_field("accessId", shared.resolve_entity_access_id)
wiki.set_field("writeAccessId", shared.resolve_entity_write_access_id)

resolvers = [wiki]
