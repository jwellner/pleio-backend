from ariadne import ObjectType
from core.tasks import get_notification_action_entity
from user.models import User


notification = ObjectType("Notification")


@notification.field("id")
def resolve_id(obj, info):
    # pylint: disable=unused-argument
    return obj.id

@notification.field("action")
def resolve_action(obj, info):
    # pylint: disable=unused-argument
    return obj.verb

@notification.field("performer")
def resolve_performer(obj, info):
    # pylint: disable=unused-argument
    return User.objects.get(id=obj.actor_object_id)

@notification.field("entity")
def resolve_entity(obj, info):
    # pylint: disable=unused-argument
    return get_notification_action_entity(obj)

@notification.field("container")
def resolve_container(obj, info):
    # pylint: disable=unused-argument
    return get_notification_action_entity(obj).group

@notification.field("timeCreated")
def resolve_timestamp(obj, info):
    # pylint: disable=unused-argument
    return obj.timestamp

@notification.field("isUnread")
def resolve_isUnread(obj, info):
    # pylint: disable=unused-argument
    return obj.unread
