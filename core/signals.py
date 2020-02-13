from django.db.models.signals import post_save
from django.conf import settings
from notifications.signals import notify
from core.models import Comment
from user.models import User
from event.models import Event
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


# TODO: we should check if user has turned notification setting on for group
def entity_handler(sender, instance, created, **kwargs):
    """ Adds notification for group members if entity in group is created

    If an entity is created in a group, a notification is added for all group
    member in this group.

    """
    # pylint: disable=unused-argument
    if not instance.group or not created:
        return
    for member in instance.group.members.filter(type__in=['admin', 'owner', 'member']):
        user = member.user
        if instance.owner == user:
            continue
        notify.send(instance.owner, recipient=user, verb='created', action_object=instance)


post_save.connect(comment_handler, sender=Comment)
post_save.connect(user_handler, sender=User)
post_save.connect(entity_handler, sender=Blog)
post_save.connect(entity_handler, sender=Discussion)
post_save.connect(entity_handler, sender=Event)
post_save.connect(entity_handler, sender=Question)
post_save.connect(entity_handler, sender=StatusUpdate)
