from django.core.management.base import BaseCommand
from django.utils import timezone
from core.lib import send_mail_multi
from core.models import User
from core import config
from core.mapper import get_notification
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Send notification emails'

    def send_notifications(self, user, notifications, subject):
        mapped_notifications = []
        for notification in notifications.values():
            mapped_notifications.append(get_notification(notification))
        if notifications:
            email = send_mail_multi(subject, 'email/send_notification_emails.html', {'notifications': mapped_notifications}, [user.email])
            email.send()
            user.notifications.mark_as_sent()

    def handle(self, *args, **kwargs):
        users = User.objects.all()

        subject = "New notifications at %s" % config.NAME

        for user in users:

            # do not send mail to disabled users
            if not user.is_active:
                continue

            # do not send mail to users that not logged in for 6 months
            if user.last_login and (user.last_login < datetime.now() - timedelta(hours=4460)):
                continue

            notifications = user.notifications.filter(emailed=False, verb__in=['created', 'commented'])[:5]
            # do not send mail when there are now new notifications
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 24 hours emailed
            time_threshold = datetime.now() - timedelta(hours=24)
            notifications_emailed_in_last_24_hours = user.notifications.filter(emailed=True, timestamp__gte=time_threshold)
            if notifications_emailed_in_last_24_hours:
                continue

            self.send_notifications(user, notifications, subject)
