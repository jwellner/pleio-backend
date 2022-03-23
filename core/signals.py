import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.conf import settings
from django.utils import timezone
from core.models.mixin import ModelWithFile
from notifications.signals import notify
from core.lib import datetime_isoformat, get_model_name, tenant_schema
from core.models import Comment, Group, GroupInvitation, Entity, EntityViewCount, NotificationMixin, MentionMixin, AttachmentMixin
from core.tasks import create_notification
from user.models import User
from event.models import EventAttendee
from notifications.models import Notification

logger = logging.getLogger(__name__)

def comment_handler(sender, instance, created, **kwargs):
    """ if comment is added to content, create a notification for all users following the content """
    # pylint: disable=unused-argument
    if not created:
        return

    if instance.owner:
        sender = instance.owner.id
    else:
        return

    container = instance.get_root_container()
    container.last_action = instance.created_at
    container.save()

    if hasattr(container, 'add_follow'):
        container.add_follow(instance.owner)

    create_notification.delay(tenant_schema(), 'commented', get_model_name(container), container.id, sender)


def user_handler(sender, instance, created, **kwargs):
    """
        Add welcome notification if user is created
    """
    # pylint: disable=unused-argument
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
    if created:
        if not instance.is_archived and issubclass(type(instance), NotificationMixin) and instance.group:
            if (not instance.published) or (datetime_isoformat(instance.published) > datetime_isoformat(timezone.now())):
                return

            create_notification.delay(tenant_schema(), 'created', get_model_name(instance), instance.id, instance.owner.id)
        else:
            instance.notifications_created = True
            instance.save()

def notification_update_handler(sender, instance, **kwargs):
    """ Delete notifications when read_access changed and user can not read entity """

    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    if not instance.group or instance._state.adding:
        return

    # check if instance has id, when copying entity, id is None
    if instance.id:
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
    if not instance._state.adding:
        instance.updated_at = timezone.now()

def mention_handler(sender, instance, created, **kwargs):
    """ Look for users that are mentioned and notify them """
    # pylint: disable=unused-argument

    if not issubclass(type(instance), MentionMixin):
        return

    if not instance.owner: # extra robustness for when tests don't assign an owner
        return

    create_notification.delay(tenant_schema(), 'mentioned', get_model_name(instance), instance.id, instance.owner.id)

def file_delete_handler(sender, instance, using, **kwargs):
    # pylint: disable=unused-argument
    instance.delete_files()

def attachment_handler(sender, instance, using, **kwargs):
    # pylint: disable=unused-argument
    instance.update_attachments_links()

def process_waitinglist_handler(sender, instance, using, **kwargs):
    # pylint: disable=unused-argument
    instance.event.process_waitinglist()


# Notification handlers
post_save.connect(comment_handler, sender=Comment)
post_save.connect(user_handler, sender=User)

# Set updated_at
pre_save.connect(updated_at_handler, sender=Comment)
pre_save.connect(updated_at_handler, sender=EntityViewCount)
pre_save.connect(updated_at_handler, sender=Group)
pre_save.connect(updated_at_handler, sender=GroupInvitation)
pre_save.connect(updated_at_handler, sender=EventAttendee)
pre_save.connect(updated_at_handler, sender=User)

# If attendee is deleted, process waitinglist
post_delete.connect(process_waitinglist_handler, sender=EventAttendee)

# Connect to all Entity subclasses
for subclass in Entity.__subclasses__():
    pre_save.connect(updated_at_handler, subclass)
    pre_save.connect(notification_update_handler, sender=subclass)
    post_save.connect(notification_handler, sender=subclass)

for subclass in MentionMixin.__subclasses__():
    post_save.connect(mention_handler, subclass)

for subclass in AttachmentMixin.__subclasses__():
    post_save.connect(attachment_handler, subclass)

for subclass in ModelWithFile.__subclasses__():
    post_delete.connect(file_delete_handler, subclass)
