from ariadne import ObjectType


column = ObjectType("Column")

@column.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@column.field("containerGuid")
def resolve_container_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.page.id

@column.field("position")
def resolve_position(obj, info):
    # pylint: disable=unused-argument
    return obj.position

@column.field("parentGuid")
def resolve_parent_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.row.guid

@column.field("width")
def resolve_is_full_width(obj, info):
    # pylint: disable=unused-argument
    return obj.width

@column.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.page.can_write(info.context["request"].user)
