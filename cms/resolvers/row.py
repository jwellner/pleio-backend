from ariadne import ObjectType


row = ObjectType("Row")

@row.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@row.field("containerGuid")
def resolve_container_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.page.id

@row.field("position")
def resolve_position(obj, info):
    # pylint: disable=unused-argument
    return obj.position

@row.field("parentGuid")
def resolve_parent_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.parent_id

@row.field("isFullWidth")
def resolve_is_full_width(obj, info):
    # pylint: disable=unused-argument
    return obj.is_full_width

@row.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.page.can_write(info.context.user)
