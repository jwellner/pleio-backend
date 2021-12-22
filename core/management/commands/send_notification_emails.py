from django.core.management.base import BaseCommand
from django.db import connection
from user.models import User
from datetime import timedelta
from django.utils import timezone
from core.services import MailService

class Command(BaseCommand):
    help = 'Send notification emails'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mail_service = MailService()

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True)

        for user in users:
            interval = user.profile.notification_email_interval_hours

            notifications = user.notifications.filter(emailed=False, verb__in=['created', 'commented'])[:5]
            # do not send mail when there are now new notifications
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 'interval' hours emailed
            time_threshold = timezone.now() - timedelta(hours=interval)
            notifications_emailed_in_last_interval_hours = user.notifications.filter(emailed=True, timestamp__gte=time_threshold)
            if notifications_emailed_in_last_interval_hours:
                continue

            self.mail_service.send_notification_email(connection.schema_name, user, notifications)
            user.notifications.mark_as_sent()
