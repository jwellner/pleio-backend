def resolve_notifications(_, info, offset=0, limit=20, unread=None):
    """ Returns notification, which are created through methods in signals.py """
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    if not user.is_authenticated:
        return {
            'total': 0,
            'totalUnread': 0,
            'edges': list(),
        }

    total_unread = user.notifications.filter(unread=True).count()

    notifications = user.notifications.all()

    if unread is False:
        notifications = notifications.filter(unread=False)
    if unread is True:
        notifications = notifications.filter(unread=True)

    edges = notifications[offset:offset+limit]

    return {
        'total': notifications.count(),
        'totalUnread': total_unread,
        'edges': edges,
    }
