from django.core.management.base import BaseCommand
from django.utils import timezone
from core.lib import send_mail_multi, get_default_email_context
from core.models import User
from core import config
from core.mapper import get_notification
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Send notification emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url', dest='url', required=True,
            help='url in notification emails',
        )

    def send_notifications(self, user, notifications, subject, site_url):

        mapped_notifications = []
        for notification in notifications.values():
            mapped_notifications.append(get_notification(notification))
        if notifications:
            site_name = config.NAME
            primary_color = config.STYLE['colorPrimary']
            context = {'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color, 'notifications': mapped_notifications}
            email = send_mail_multi(subject, 'email/send_notification_emails.html', context, [user.email])
            email.send()
            user.notifications.mark_as_sent()

    def handle(self, *args, **options):
        site_url = options['url']
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
            time_threshold = datetime.now()  - timedelta(hours=24)
            notifications_emailed_in_last_24_hours = user.notifications.filter(emailed=True, timestamp__gte=time_threshold)
            if notifications_emailed_in_last_24_hours:
                continue

            self.send_notifications(user, notifications, subject, site_url)
