from ariadne import ObjectType

user = ObjectType("User")

@user.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return "/user/{}/profile".format(obj.guid)

@user.field("profile")
def resolve_profile(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("stats")
def resolve_stats(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("groupNotifications")
def resolve_group_notifications(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("canEdit")
def resolve_can_edit(obj, info):
    return info.context.user == obj