from core.mapper import get_notification


def get_notifications(user, offset=0, limit=20):
    result = []
    notifications = user.notifications.all()[offset:offset+limit].values()
    for notification in notifications:
        result.append(get_notification(notification))
    return result


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

    edges = get_notifications(user)

    total_unread = len([item for item in edges if item['isUnread']])
    return {
        'total': len(edges),
        'totalUnread': total_unread,
        'edges': edges,
    }
