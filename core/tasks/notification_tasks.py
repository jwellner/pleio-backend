from celery import shared_task
from core.models.entity import Entity
from core.models.group import GroupMembership
from core.lib import tenant_schema
from django.utils import timezone
from django_tenants.utils import schema_context
from notifications.signals import notify
from user.models import User
from core.models.mixin import NotificationMixin
from notifications.models import Notification
from core.services.mail_service import MailService

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

            create_notification.delay(tenant_schema(), 'created', instance.id, instance.owner.id)


@shared_task(bind=True, ignore_result=True)
def create_notification(self, schema_name, verb, entity_id, sender_id):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    '''
    task for creating a notification. If the content of the notification is in a group and the recipient has configured direct notifications
    for this group. An email task wil be triggered with this notification
    '''
    with schema_context(schema_name):
        instance = Entity.objects.get_subclass(id=entity_id)
        sender = User.objects.get(id=sender_id)

        if verb == "created":
            recipients = []
            if instance.group:
                for member in instance.group.members.filter(type__in=['admin', 'owner', 'member']).exclude(notification_mode='disable'):
                    if sender == member.user:
                        continue
                    if not instance.can_read(member.user):
                        continue
                    recipients.append(member.user)
        elif verb == "commented":
            recipients = []
            if hasattr(instance, 'followers'):
                for follower in instance.followers():
                    if sender == follower:
                        continue
                    if not instance.can_read(follower):
                        continue
                    recipients.append(follower)
        else:
            return

        # tuple with list is returned, get the notification created
        notifications = notify.send(sender, recipient=recipients, verb=verb, action_object=instance)[0][1]

        instance.notifications_created = True
        instance.save()

        # only send direct notification for content in groups
        if instance.group:
            mail_service = MailService()
            for notification in notifications:
                recipient = User.objects.get(id=notification.recipient_id)
                direct = False
                # get direct setting
                try:
                    direct = GroupMembership.objects.get(user=recipient, group=instance.group).notification_mode == 'direct'
                except Exception:
                    continue

                # send email direct and mark emailed as True
                if direct:
                    mail_service.send_notification_email(schema_name, recipient, [notification])
