from ariadne import ObjectType
from core.resolvers import shared


page = ObjectType("Page")

@page.field("pageType")
def resolve_page_type(obj, info):
    # pylint: disable=unused-argument
    return obj.page_type

@page.field("hasChildren")
def resolve_has_children(obj, info):
    # pylint: disable=unused-argument
    return obj.has_children()

@page.field("children")
def resolve_children(obj, info):
    # pylint: disable=unused-argument
    return obj.children.visible(info.context["request"].user)

@page.field("parent")
def resolve_parent(obj, info):
    # pylint: disable=unused-argument
    return obj.parent

@page.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@page.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.can_write(info.context["request"].user)

@page.field("rows")
def resolve_rows(obj, info):
    # pylint: disable=unused-argument
    return obj.rows.all()

@page.field("columns")
def resolve_columns(obj, info):
    # pylint: disable=unused-argument
    return obj.columns.all()

@page.field("widgets")
def resolve_widgets(obj, info):
    # pylint: disable=unused-argument
    return obj.widgets.all()


page.set_field("guid", shared.resolve_entity_guid)
page.set_field("status", shared.resolve_entity_status)
page.set_field("title", shared.resolve_entity_title)
page.set_field("description", shared.resolve_entity_description)
page.set_field("richDescription", shared.resolve_entity_rich_description)
page.set_field("excerpt", shared.resolve_entity_excerpt)
page.set_field("tags", shared.resolve_entity_tags)
page.set_field("timeCreated", shared.resolve_entity_time_created)
page.set_field("timeUpdated", shared.resolve_entity_time_updated)
page.set_field("accessId", shared.resolve_entity_access_id)
page.set_field("isPinned", shared.resolve_entity_is_pinned)
