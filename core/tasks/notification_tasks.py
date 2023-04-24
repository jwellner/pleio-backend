import logging
from celery import shared_task
from core import config
from core.models.entity import Entity
from core.models.group import GroupMembership
from core.models.push_notification import WebPushSubscription
from core.lib import get_model_name, tenant_schema
from core.utils.push_notification import get_notification_payload, send_web_push_notification
from django.apps import apps
from django.utils import timezone, translation
from django_tenants.utils import schema_context
from notifications.signals import notify

from user.models import User
from core.models.mixin import NotificationMixin
from notifications.models import Notification

LOGGER = logging.getLogger(__name__)


@shared_task()
def create_notifications_for_scheduled_content(schema_name):
    with schema_context(schema_name):

        for instance in Entity.objects.filter(notifications_created=False, published__lte=timezone.now()).exclude(published=None).select_subclasses():
            # instance has no NotificationMixin impemented. Set notifications_created True so it is skipped next time.
            if instance.__class__ not in NotificationMixin.__subclasses__():
                instance.notifications_created = True
                instance.save()
                continue

            # instance has no group. Set notifications_created True so it is skipped next time.
            if not instance.group:
                instance.notifications_created = True
                instance.save()
                continue

            # there are already notifications for this instance.id. Set notifications_created True so it is skipped next time.
            if Notification.objects.filter(action_object_object_id=instance.id).count() > 0:
                instance.notifications_created = True
                instance.save()
                continue

            create_notification.delay(tenant_schema(), 'created', get_model_name(instance), instance.id, instance.owner.id)


@shared_task(bind=True, ignore_result=True)
def create_notification(self, schema_name, verb, model_name, entity_id, sender_id):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks
    '''
    task for creating a notification. If the content of the notification is in a group and the recipient has configured direct notifications
    for this group. An email task wil be triggered with this notification
    '''
    with schema_context(schema_name):
        Model = apps.get_model(model_name)
        instance = Model.objects.filter(id=entity_id).first()
        sender = User.objects.filter(id=sender_id).first()

        if not instance:
            LOGGER.warning('Entity with id %s does not exist.')
            return

        if not sender:  # sender is probably no active user don't create notifications for inactive users
            LOGGER.warning('Sender with id %s is not active.')
            return

        if verb == "created":
            recipients = []
            if instance.group:
                for member in instance.group.members.filter(type__in=['admin', 'owner', 'member']).exclude(is_notifications_enabled=False):
                    if sender == member.user:
                        continue
                    if not instance.can_read(member.user):
                        continue
                    recipients.append(member.user)

            if not instance.notifications_created:
                instance.notifications_created = True
                instance.save()

        elif verb == "commented":
            recipients = []
            if hasattr(instance, 'followers'):
                for follower in instance.followers():
                    if sender == follower:
                        continue
                    if not instance.can_read(follower):
                        continue
                    recipients.append(follower)
        elif verb == 'mentioned':
            recipients = User.objects.get_unmentioned_users(instance.mentioned_users, instance)
        elif verb == 'custom':
            recipients = instance.recipients()
        else:
            return

        # tuple with list is returned, get the notification created
        notifications = notify.send(sender, recipient=recipients, verb=verb, action_object=instance)[0][1]

        # only send direct and push notification for content in groups
        if getattr(instance, 'group', None):
            from core.mail_builders.notifications import schedule_notification_mail, MailTypeEnum
            for notification in notifications:
                try:
                    recipient = User.objects.get(id=notification.recipient_id)
                    membership = GroupMembership.objects.get(user=recipient, group=instance.group)
                except Exception:
                    continue

                # send email direct and mark emailed as True
                if membership.is_notification_direct_mail_enabled:
                    schedule_notification_mail(recipient, [notification], MailTypeEnum.DIRECT)

                # send push notification
                if membership.is_notification_push_enabled and config.PUSH_NOTIFICATIONS_ENABLED:
                    translation.activate(recipient.get_language())
                    payload = get_notification_payload(sender, verb, instance)
                    if payload:
                        for subscription in WebPushSubscription.objects.filter(user=recipient):
                            send_web_push_notification(subscription, payload)
