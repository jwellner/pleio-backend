from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django.utils import timezone
from notifications.signals import notify
from core.models import Comment, Group, GroupInvitation, Entity, EntityViewCount
from user.models import User
from event.models import Event, EventAttendee
from blog.models import Blog
from discussion.models import Discussion
from question.models import Question
from activity.models import StatusUpdate


def comment_handler(sender, instance, created, **kwargs):
    """ if comment is added to content, create a notification for all users following the content """
    # pylint: disable=unused-argument
    if not created:
        return
    users = User.objects.filter(annotation__key='followed', annotation__object_id=instance.object_id).exclude(id=instance.owner.id)
    notify.send(instance.owner, recipient=users, verb='commented', action_object=instance.container)


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


def entity_handler(sender, instance, created, **kwargs):
    """ Adds notification for group members if entity in group is created

    If an entity is created in a group, a notification is added for all group
    member in this group.

    """

    # pylint: disable=unused-argument
    if not instance.group or not created:
        return
    for member in instance.group.members.filter(type__in=['admin', 'owner', 'member'], enable_notification=True):
        if instance.owner == member.user:
            continue
        notify.send(instance.owner, recipient=member.user, verb='created', action_object=instance)


def updated_at_handler(sender, instance, **kwargs):
    """ This adds the current date/time to updated_at only when the instance is updated

    This way we can still set the updated_at date/time when importing data.
    """

    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    if not instance._state.adding:
        instance.updated_at = timezone.now()


# Notification handlers
post_save.connect(comment_handler, sender=Comment)
post_save.connect(user_handler, sender=User)
post_save.connect(entity_handler, sender=Blog)
post_save.connect(entity_handler, sender=Discussion)
post_save.connect(entity_handler, sender=Event)
post_save.connect(entity_handler, sender=Question)
post_save.connect(entity_handler, sender=StatusUpdate)

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
