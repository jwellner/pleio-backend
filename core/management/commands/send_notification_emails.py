from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy
from django.db import connection
from user.models import User
from core import config
from core.models import Entity
from datetime import datetime, timedelta
from tenants.models import Client
from django.utils import translation
from core.tasks import send_mail_multi, get_notification


class Command(BaseCommand):
    help = 'Send notification emails'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def send_notifications(self, user, notifications, subject, site_url, show_excerpt):

        mapped_notifications = []
        for notification in notifications:
            mapped_notifications.append(get_notification(notification))
        if notifications:
            site_name = config.NAME
            user_url = site_url + '/user/' + user.guid + '/settings'
            primary_color = config.COLOR_PRIMARY
            header_color = config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY
            context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                       'header_color': header_color, 'notifications': mapped_notifications, 'show_excerpt': show_excerpt}

            send_mail_multi.delay(connection.schema_name, subject, 'email/send_notification_emails.html', context, user.email)

            user.notifications.mark_as_sent()

    def handle(self, *args, **options):
        tenant = Client.objects.get(schema_name=connection.schema_name)

        site_url = 'https://' + tenant.domains.first().domain

        users = User.objects.filter(is_active=True, _profile__receive_notification_email=True)

        show_excerpt = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
        subject = ugettext_lazy("New notifications at %(site_name)s") % {'site_name': config.NAME}

        for user in users:

            notifications = user.notifications.filter(emailed=False, verb__in=['created', 'commented'])[:5]
            # do not send mail when there are now new notifications
            if not notifications:
                continue

            # do not send a mail when there is an notification less old than 24 hours emailed
            time_threshold = datetime.now() - timedelta(hours=4)
            notifications_emailed_in_last_4_hours = user.notifications.filter(emailed=True, timestamp__gte=time_threshold)
            if notifications_emailed_in_last_4_hours:
                continue

            self.send_notifications(user, notifications, subject, site_url, show_excerpt)
