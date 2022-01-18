from ariadne import ObjectType

notifications_list = ObjectType("NotificationsList")

@notifications_list.field("total")
def resolve_total(query, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user

    if not user.is_authenticated:
        return 0

    unread = query.get("unread", None)

    if unread is False:
        notifications = user.notifications.filter(unread=False)
    elif unread is True:
        notifications = user.notifications.filter(unread=True)
    else:
        notifications = user.notifications.all()

    return notifications.count()
   
@notifications_list.field("edges")
def resolve_edges(query, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user

    if not user.is_authenticated:
        return []

    offset = query.get("offset", 0)
    limit = query.get("limit", 20)
    unread = query.get("unread", None)

    if unread is False:
        notifications = user.notifications.filter(unread=False)
    elif unread is True:
        notifications = user.notifications.filter(unread=True)
    else:
        notifications = user.notifications.all()

    edges = notifications[offset:offset+limit]

    return edges

@notifications_list.field("totalUnread")
def resolve_total_unread(query, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user

    if not user.is_authenticated:
        return 0

    return user.notifications.filter(unread=True).count()
