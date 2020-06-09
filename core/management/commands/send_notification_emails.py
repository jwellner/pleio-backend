from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from core.lib import send_mail_multi, get_default_email_context
from user.models import User
from core import config
from datetime import datetime, timedelta
from core.resolvers.notification import get_notification_action_entity


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

    def add_arguments(self, parser):
        parser.add_argument(
            '--url', dest='url', required=True,
            help='url in notification emails',
        )

    def send_notifications(self, user, notifications, subject, site_url):

        mapped_notifications = []
        for notification in notifications:
            mapped_notifications.append(get_notification(notification))
        if notifications:
            site_name = config.NAME
            user_url = site_url + '/user/' + user.guid + '/settings'
            primary_color = config.COLOR_PRIMARY
            context = {'user_url': user_url, 'site_name': site_name, 'site_url': site_url, 'primary_color': primary_color,
                       'notifications': mapped_notifications}
            email = send_mail_multi(subject, 'email/send_notification_emails.html', context, [user.email])
            email.send()
            user.notifications.mark_as_sent()

    def handle(self, *args, **options):
        site_url = options['url']
        users = User.objects.filter(is_active=True)

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

            self.send_notifications(user, notifications, subject, site_url)
