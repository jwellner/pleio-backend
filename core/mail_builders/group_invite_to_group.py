from django.utils.translation import gettext

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_invite_to_group_mail(user, sender, email, language, group):
    from core.models import MailInstance
    assert user or (email and language), "Provide either a user or email and language properties"
    MailInstance.objects.submit(InviteToGroupMailer, {
        "email": email,
        "language": language,
        "user": user.guid if user else None,
        "sender": sender.guid,
        "group": group.guid
    })


class InviteToGroupMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.email = kwargs.get('email')
        self.language = kwargs.get('language')
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs.get('user') else None
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User']) if kwargs.get('sender') else None
        self.group = load_entity_by_id(kwargs.get('group'), ['core.Group'])

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['link'] = get_full_url(self.group.url)
        context['group_name'] = self.group.name
        return context

    def get_language(self):
        return self.language or self.user.get_language()

    def get_template(self):
        return "email/invite_to_group.html"

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.email or self.user.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return gettext("Invitation to become a member of the %(group_name)s group") % {
            'group_name': self.group.name
        }
