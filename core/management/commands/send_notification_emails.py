from django.core.management.base import BaseCommand
from django.utils import translation
from django.utils.translation import ugettext_lazy
from django.db import connection
from user.models import User
from core import config
from core.lib import get_default_email_context, map_notification
from datetime import datetime, timedelta
from django.utils import translation
from core.tasks import send_mail_multi

class Command(BaseCommand):
    help = 'Send notification emails'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def send_notification_email(self, user, notifications, subject):

        mapped_notifications = []
        for notification in notifications:
            mapped_notifications.append(map_notification(notification))

        if notifications:
            context = get_default_email_context(user)
            context['user_url'] = user.url + '/settings'
            context['show_excerpt'] = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
            context['notifications'] = mapped_notifications

            send_mail_multi.delay(connection.schema_name, subject, 'email/send_notification_emails.html', context, user.email)
            
            user.notifications.mark_as_sent()

    def handle(self, *args, **options):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)

        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True)

        for user in users:

            interval = user.profile.notification_email_interval_hours

            translation.activate(user.get_language())
            subject = ugettext_lazy("New notifications at %(site_name)s") % {'site_name': config.NAME}

            notifications = user.notifications.filter(emailed=False, verb__in=['created', 'commented'])[:5]
            # do not send mail when there are now new notifications
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 'interval' hours emailed
            time_threshold = datetime.now() - timedelta(hours=interval)
            notifications_emailed_in_last_interval_hours = user.notifications.filter(emailed=True, timestamp__gte=time_threshold)
            if notifications_emailed_in_last_interval_hours:
                continue

            self.send_notification_email(user, notifications, subject)
