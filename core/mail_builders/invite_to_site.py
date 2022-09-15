from django.utils.html import format_html
from django.utils.translation import gettext as _

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.models import SiteInvitation
from core.utils.entity import load_entity_by_id


def schedule_invite_to_site_mail(email, message, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(InviteToSiteMailer, {
        'sender': sender.guid,
        'email': email,
        'message': message,
    })


class InviteToSiteMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])
        self.email = kwargs['email']
        self.message = kwargs['message']

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['link'] = self.build_link()
        context['message'] = format_html(self.message) or ''
        return context

    def build_link(self):
        code = SiteInvitation.objects.get(email=self.email).code
        return get_full_url('/login?invitecode=' + code)

    def get_language(self):
        return config.LANGUAGE

    def get_template(self):
        return "email/invite_to_site.html"

    def get_receiver(self):
        return None

    def get_receiver_email(self):
        return self.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return _("You are invited to join site %(site_name)s") % {'site_name': config.NAME}
