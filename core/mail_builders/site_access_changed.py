from django.utils.translation import gettext as _

from core import config
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_site_access_changed_mail(is_closed, admin, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(SiteAccessChangedMailer, {
        'is_closed': is_closed,
        'admin': admin.guid,
        'sender': sender.guid,
    })


class SiteAccessChangedMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin = load_entity_by_id(kwargs['admin'], ['user.User'])
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])
        self.is_closed = kwargs['is_closed']

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['access_level'] = _('closed') if self.is_closed else _('public')
        return context

    def get_language(self):
        return self.admin.get_language()

    def get_template(self):
        return "email/site_access_changed.html"

    def get_receiver(self):
        return self.admin

    def get_receiver_email(self):
        return self.admin.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return _("Site access level changed for %(site_name)s") % {'site_name': config.NAME}
