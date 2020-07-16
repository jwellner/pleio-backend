from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy
from django.db import connection
from core.lib import send_mail_multi, get_default_email_context
from user.models import User
from core import config
from datetime import datetime, timedelta
from core.resolvers.notification import get_notification_action_entity
from tenants.models import Client

def get_notification(notification):
    """ get a mapped notification """
    entity = get_notification_action_entity(notification)
    performer = User.objects.get(id=notification.actor_object_id)

    return {
        'id': notification.id,
        'action': notification.verb,
        'performer': performer,
        'entity': entity,
        'container': entity.group,
        'timeCreated': notification.timestamp,
        'isUnread': notification.unread
    }


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
            context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                       'notifications': mapped_notifications, 'show_excerpt': show_excerpt}
            email = send_mail_multi(subject, 'email/send_notification_emails.html', context, [user.email])
            email.send()
            user.notifications.mark_as_sent()

    def handle(self, *args, **options):
        tenant = Client.objects.get(schema_name=connection.schema_name)

        site_url = 'https://' + tenant.domains.first().domain

        users = User.objects.filter(is_active=True)

        show_excerpt = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
        subject = ugettext_lazy("New notifications at %s" % config.NAME)

        for user in users:

            # do not send mail to disabled users
            if not user.is_active:
                continue

            # do not send mail to users that not logged in for 6 months
            if user.profile and user.profile.last_online and (user.profile.last_online < (datetime.now() - timedelta(hours=4460))):
                continue

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
