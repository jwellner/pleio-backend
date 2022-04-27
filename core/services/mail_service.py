from core import config
from django.utils import translation
from core.lib import get_default_email_context, map_notification
from core.tasks.mail_tasks import send_mail_multi
from notifications.models import Notification


class MailTypeEnum:
    DIRECT = 'direct'
    COLLECTED = 'collected'


class MailService:

    def __init__(self, mail_type: MailTypeEnum):
        self.mail_type = mail_type

    def send_notification_email(self, schema_name, recipient, notifications):
        if not notifications:
            return

        translation.activate(recipient.get_language())

        # Do not send mail when notifications are disabled, but mark as send (so when enabled you dont receive old notifications!)
        if recipient.profile.receive_notification_email:
            subject = self.get_notification_subject(notifications)
            context = self.get_notification_context(recipient, notifications)

            send_mail_multi.delay(schema_name, subject, 'email/send_notification_emails.html', context, recipient.email)

        # Mark notifications as send regardless of user setting (so when enabled you dont receive old notifications!)
        Notification.objects.filter(id__in=[notification.id for notification in notifications]).update(emailed=True)

    def get_notification_subject(self, notifications):
        subject = ""
        if len(notifications) == 1:
            notification = map_notification(notifications[0])
            if notification['entity_title']:
                subject = translation.ugettext_lazy("Notification on %(entity_title)s") % {
                    'entity_title': notification['entity_title']}
            elif notification['entity_group']:
                subject = translation.ugettext_lazy(
                    "Notification on %(entity_type)s in group %(entity_group_name)s") % {
                              'entity_type': notification['entity_type'],
                              'entity_group_name': notification['entity_group_name']
                          }
            else:
                # Keeping the variable the same is on purpose so it can use the same translation
                subject = translation.ugettext_lazy("Notification on %(entity_title)s") % {
                    'entity_title': notification['entity_type']}
        else:
            subject = translation.ugettext_lazy("New notifications at %(site_name)s") % {'site_name': config.NAME}

        return subject

    def get_notification_context(self, recipient, notifications):
        mapped_notifications = []
        for notification in notifications:
            mapped_notifications.append(map_notification(notification))

        context = get_default_email_context(recipient)
        context['show_excerpt'] = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
        context['notifications'] = mapped_notifications
        context['mail_type'] = self.mail_type

        return context
