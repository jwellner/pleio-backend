import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.lib import tenant_schema, is_schema_public
from user.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send notification emails'

    def handle(self, *args, **options):
        if is_schema_public():
            return

        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True)

        for user in users:
            interval = user.profile.notification_email_interval_hours

            time_threshold = timezone.now() - timedelta(hours=interval)
            notifications = user.notifications.filter(emailed=False, timestamp__gte=time_threshold, verb__in=['created', 'commented', 'mentioned'])[:20]
            # Do not send mail when there are no new notifications.
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 'interval' hours emailed
            notifications_emailed_in_last_interval_hours = user.notifications.filter(emailed=True,
                                                                                     timestamp__gte=time_threshold)
            if notifications_emailed_in_last_interval_hours:
                continue

            from core.mail_builders.notifications import (MailTypeEnum,
                                                          schedule_notification_mail)
            try:
                schedule_notification_mail(user, notifications, MailTypeEnum.COLLECTED)
            except Exception as e:
                logger.error("send_notifications error %s %s %s %s", tenant_schema(), user.email, e.__class__, e)
                continue

            user.notifications.filter(id__in=notifications).mark_as_sent()
