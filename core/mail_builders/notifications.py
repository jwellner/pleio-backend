from django.apps import apps
from django.utils.translation import ugettext as _
from notifications.models import Notification

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.mail import UnsubscribeTokenizer


class MailTypeEnum:
    DIRECT = 'direct'
    COLLECTED = 'collected'


def schedule_notification_mail(user, notifications, mail_type):
    from core.models import MailInstance
    MailInstance.objects.submit(NotificationsMailer, {
        'user': user.guid,
        'notifications': [n.pk for n in notifications],
        'mail_type': mail_type,
    })


class NotificationsMailer(TemplateMailerBase):

    _unsubscribe_url = None

    def __init__(self, **kwargs):
        from user.models import User
        super().__init__(**kwargs)
        self.user: User = User.objects.get(id=kwargs['user'])
        self.notifications = self._load_notifications(kwargs['notifications'])
        self.mail_type = kwargs['mail_type']

    @staticmethod
    def _load_notifications(pks):
        notifications = Notification.objects.filter(pk__in=pks)
        return [serialize_notification(n) for n in notifications]

    def get_context(self):
        context = self.build_context(user=self.user)
        context['show_excerpt'] = config.EMAIL_NOTIFICATION_SHOW_EXCERPT
        context['notifications'] = self.notifications
        context['mail_type'] = self.mail_type
        context['unsubscribe_url'] = self.unsubscribe_url
        return context

    def get_headers(self):
        headers = super().get_headers()
        headers['List-Unsubscribe'] = self.unsubscribe_url
        return headers

    @property
    def unsubscribe_url(self):
        if not self._unsubscribe_url:
            tokenizer = UnsubscribeTokenizer()
            url = tokenizer.create_url(self.user, tokenizer.TYPE_NOTIFICATIONS)
            self._unsubscribe_url = get_full_url(url)
        return self._unsubscribe_url

    def get_subject(self):
        if len(self.notifications) == 1:
            notification = self.notifications[0]
            if notification['entity_title']:
                return _("Notification on %(entity_title)s") % {
                    'entity_title': notification['entity_title']
                }
            if notification['entity_group']:
                return _("Notification on %(entity_type)s in group %(entity_group_name)s") % {
                    'entity_type': notification['entity_type'],
                    'entity_group_name': notification['entity_group_name']
                }
            # Keeping the variable the same is on purpose so it can use the same translation
            return _("Notification on %(entity_title)s") % {
                'entity_title': notification['entity_type']
            }
        return _("New notifications at %(site_name)s") % {'site_name': config.NAME}

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return 'email/send_notification_emails.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return None


def serialize_notification(notification):
    """ get a mapped notification """
    entity = notification.action_object
    performer = apps.get_model('user.User').objects.with_deleted().get(id=notification.actor_object_id)
    entity_group = False
    entity_group_name = ""
    entity_group_url = ""
    if hasattr(entity, 'group') and entity.group:
        entity_group = True
        entity_group_name = entity.group.name
        entity_group_url = entity.group.url

    return {
        'id': notification.id,
        'action': notification.verb,
        'performer_name': performer.name,
        'entity_title': entity.title if hasattr(entity, 'title') else "",
        'entity_description': entity.description if hasattr(entity, 'description') else "",
        'entity_type': entity._meta.verbose_name,
        'entity_group': entity_group,
        'entity_group_name': entity_group_name,
        'entity_group_url': entity_group_url,
        'entity_url': entity.url,
        'type_to_string': entity.type_to_string,
        'timeCreated': notification.timestamp,
        'isUnread': notification.unread
    }
