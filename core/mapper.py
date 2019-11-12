from core.models import Entity, User


def get_notification_action_entity(notification):
    """ get entity from actoin_object_object_id """
    try:
        entity = Entity.objects.get_subclass(id=notification['action_object_object_id'])
    except Exception:
        entity = User.objects.get(id=notification['actor_object_id'])
        entity.group = None

    return entity


def get_notification(notification):
    """ get a mapped notification """
    entity = get_notification_action_entity(notification)
    performer = User.objects.get(id=notification['actor_object_id'])
    return {
        'id': notification['id'],
        'action': notification['verb'],
        'performer': performer,
        'entity': entity,
        'container': entity.group,
        'timeCreated': notification['timestamp'],
        'isUnread': notification['unread']
    }
