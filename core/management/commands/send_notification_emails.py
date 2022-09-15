from django.core.management.base import BaseCommand

from core.lib import is_schema_public
from user.models import User
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Send notification emails'

    def handle(self, *args, **options):
        if is_schema_public():
            return

        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True)

        for user in users:
            interval = user.profile.notification_email_interval_hours

            notifications = user.notifications.filter(emailed=False, verb__in=['created', 'commented', 'mentioned'])[:5]
            # Do not send mail when there are no new notifications.
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 'interval' hours emailed
            time_threshold = timezone.now() - timedelta(hours=interval)
            notifications_emailed_in_last_interval_hours = user.notifications.filter(emailed=True,
                                                                                     timestamp__gte=time_threshold)
            if notifications_emailed_in_last_interval_hours:
                continue

            from core.mail_builders.notifications import schedule_notification_mail, MailTypeEnum
            schedule_notification_mail(user, notifications, MailTypeEnum.COLLECTED)

            user.notifications.mark_as_sent()
