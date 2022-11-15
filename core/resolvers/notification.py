from ariadne import ObjectType
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
    return User.objects.with_deleted().get(id=obj.actor_object_id)


@notification.field("entity")
def resolve_entity(obj, info):
    # pylint: disable=unused-argument
    if not obj.action_object or obj.verb == 'custom':
        return None
    return obj.action_object


@notification.field("customMessage")
def resolve_custom_message(obj, info):
    # pylint: disable=unused-argument
    if obj.verb != 'custom':
        return

    return obj.action_object.custom_message()


@notification.field("container")
def resolve_container(obj, info):
    # pylint: disable=unused-argument
    if obj.action_object and hasattr(obj.action_object, 'group'):
        return obj.action_object.group

    return None


@notification.field("timeCreated")
def resolve_timestamp(obj, info):
    # pylint: disable=unused-argument
    return obj.timestamp


@notification.field("isUnread")
def resolve_isUnread(obj, info):
    # pylint: disable=unused-argument
    return obj.unread
