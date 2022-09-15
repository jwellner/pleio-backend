from django.utils.translation import gettext

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_change_group_ownership_mail(user, sender, group):
    from core.models import MailInstance
    MailInstance.objects.submit(ChangeGroupOwnershipMailer, {
        "user": user.guid,
        "sender": sender.guid,
        "group": group.guid,
    })


class ChangeGroupOwnershipMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User'])
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])
        self.group = load_entity_by_id(kwargs['group'], ['core.Group'])

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['link'] = get_full_url(self.group.url)
        context['group_name'] = self.group.name
        return context

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return 'email/group_ownership_transferred.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return gettext("Ownership of the %(group_name)s group has been transferred") % {
            'group_name': self.group.name
        }
