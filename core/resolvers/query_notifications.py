def resolve_notifications(_, info, offset=0, limit=20):
    """ Returns notification, which are created through methods in signals.py """
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context.user

    if not user.is_authenticated:
        return {
            'total': 0,
            'totalUnread': 0,
            'edges': list(),
        }

    edges = user.notifications.all()[offset:offset+limit]

    total_unread = len([item for item in edges if item.unread])
    return {
        'total': len(edges),
        'totalUnread': total_unread,
        'edges': edges,
    }
