from django.utils.translation import gettext as _

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_site_access_request_mail(name, admin):
    from core.models import MailInstance
    MailInstance.objects.submit(SiteAccessRequestMailer, {
        'name': name,
        'admin': admin.guid
    })


class SiteAccessRequestMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs['name']
        self.admin = load_entity_by_id(kwargs['admin'], ['user.User'])

    def get_context(self):
        context = self.build_context()
        context['request_name'] = self.name
        context['site_admin_url'] = get_full_url("/admin/users/access-requests")
        context['admin_name'] = self.admin.name
        return context

    def get_language(self):
        return self.admin.get_language()

    def get_template(self):
        return "email/site_access_request.html"

    def get_receiver(self):
        return self.admin

    def get_receiver_email(self):
        return self.admin.email

    def get_sender(self):
        return None

    def get_subject(self):
        return _("New access request for %(site_name)s") % {'site_name': config.NAME}
