from ariadne import ObjectType

widget = ObjectType("Widget")


@widget.field("guid")
def resolve_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@widget.field("containerGuid")
def resolve_container_guid(obj, info):
    # pylint: disable=unused-argument
    # TODO: implement widget with container page
    return obj.group.guid

@widget.field("position")
def resolve_position(obj, info):
    # pylint: disable=unused-argument
    return obj.position

@widget.field("settings")
def resolve_settings(obj, info):
    # pylint: disable=unused-argument
    return obj.settings

@widget.field("canEdit")
def resolve_can_edit(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.can_write(info.context.user)
    except AttributeError:
        return False

@widget.field("parentGuid")
def resolve_parent_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.parent_id
