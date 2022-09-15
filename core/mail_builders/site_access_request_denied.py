from django.utils.translation import gettext as _

from core import config
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_site_access_request_denied_mail(email, name, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(SiteAccessRequestDeniedMailer, {
        'email': email,
        'name': name,
        'sender': sender.guid
    })


class SiteAccessRequestDeniedMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.email = kwargs['email']
        self.name = kwargs['name']
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['request_name'] = self.name
        context['intro'] = config.SITE_MEMBERSHIP_DENIED_INTRO
        return context

    def get_language(self):
        return config.LANGUAGE

    def get_template(self):
        return "email/site_access_request_denied.html"

    def get_receiver(self):
        return None

    def get_receiver_email(self):
        return self.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return _("Membership request declined for: %(site_name)s") % {'site_name': config.NAME }
