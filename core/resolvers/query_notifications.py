from core.models import Entity, User


def get_notification_action_object_entity(notification):
    if notification['action_object_object_id']:
        entity = Entity.objects.get_subclass(id=notification['action_object_object_id'])
    else:
        entity = User.objects.get(id=notification['actor_object_id'])
        entity.group = None
    return entity


def get_notifications(user, offset=0, limit=20):
    result = []
    notifications = user.notifications.all()[offset:offset+limit].values()
    for notification in notifications:
        entity = get_notification_action_object_entity(notification)
        performer = User.objects.get(id=notification['actor_object_id'])
        result.append({
            'id': notification['id'],
            'action': notification['verb'],
            'performer': performer,
            'entity': entity,
            'container': entity.group,
            'timeCreated': notification['timestamp'],
            'isUnread': notification['unread']
        })
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
