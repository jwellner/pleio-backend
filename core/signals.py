import logging
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django.utils import timezone
from notifications.signals import notify
from core.lib import tenant_schema
from core.models import Comment, Group, GroupInvitation, Entity, EntityViewCount, NotificationMixin
from core.tasks import create_notification
from user.models import User
from event.models import EventAttendee
from notifications.models import Notification

logger = logging.getLogger(__name__)

def comment_handler(sender, instance, created, **kwargs):
    """ if comment is added to content, create a notification for all users following the content """
    # pylint: disable=unused-argument
    if not settings.IMPORTING:
        if not created:
            return

        # set container last_action
        instance.container.last_action = instance.created_at
        instance.container.save()

        user_ids = []
        followers = User.objects.filter(
            annotation__key='followed',
            annotation__object_id=instance.object_id).exclude(id=instance.owner.id)

        for follower in followers:
            if not instance.container.can_read(follower):
                continue
            user_ids.append(follower.id)

        create_notification.delay(tenant_schema(), 'commented', instance.container.id, instance.owner.id, user_ids)


def user_handler(sender, instance, created, **kwargs):
    """
        Add welcome notification if user is created
    """
    # pylint: disable=unused-argument
    if not settings.IMPORTING:
        if not created or settings.RUN_AS_ADMIN_APP:
            return

        notify.send(instance, recipient=instance, verb='welcome', action_object=instance)

        # Auto join groups where is_auto_membership_enabled
        for group in Group.objects.filter(is_auto_membership_enabled=True):
            group.join(instance)


def notification_handler(sender, instance, created, **kwargs):
    """ Adds notification for group members if entity in group is created

    If an entity is created in a group, a notification is added for all group
    member in this group.

    """

    # pylint: disable=unused-argument
    if not settings.IMPORTING:
        if not instance.group or not created:
            return

        user_ids = []
        for member in instance.group.members.filter(type__in=['admin', 'owner', 'member'], enable_notification=True):
            user = member.user
            if instance.owner == user:
                continue
            if not instance.can_read(user):
                continue
            user_ids.append(user.id)

        create_notification.delay(tenant_schema(), 'created', instance.id, instance.owner.id, user_ids)

def notification_update_handler(sender, instance, **kwargs):
    """ Delete notifications when read_access changed and user can not read entity """

    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    if not settings.IMPORTING:
        if not instance.group or instance._state.adding:
            return

        entity = Entity.objects.get(id=instance.id)

        if entity.read_access != instance.read_access:
            for notification in Notification.objects.filter(action_object_object_id=instance.id):
                if not instance.can_read(notification.recipient):
                    notification.delete()

def updated_at_handler(sender, instance, **kwargs):
    """ This adds the current date/time to updated_at only when the instance is updated

    This way we can still set the updated_at date/time when importing data.
    """

    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    if not instance._state.adding and not settings.IMPORTING:
        instance.updated_at = timezone.now()


# Notification handlers
post_save.connect(comment_handler, sender=Comment)
post_save.connect(user_handler, sender=User)

# connect Models that implemented NotificationMixin
for subclass in NotificationMixin.__subclasses__():
    post_save.connect(notification_handler, sender=subclass)
    pre_save.connect(notification_update_handler, sender=subclass)

# Set updated_at
pre_save.connect(updated_at_handler, sender=Comment)
pre_save.connect(updated_at_handler, sender=EntityViewCount)
pre_save.connect(updated_at_handler, sender=Group)
pre_save.connect(updated_at_handler, sender=GroupInvitation)
pre_save.connect(updated_at_handler, sender=EventAttendee)
pre_save.connect(updated_at_handler, sender=User)

# Connect to all Entity subclasses
for subclass in Entity.__subclasses__():
    pre_save.connect(updated_at_handler, subclass)
