from django.utils.translation import gettext as _

from core.lib import get_base_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_file_scan_found_mail(virus_count, admin):
    from core.models import MailInstance
    MailInstance.objects.submit(FileScanFoundMailer, {
        'virus_count': virus_count,
        'admin': admin.guid,
    })


class FileScanFoundMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.admin = load_entity_by_id(kwargs['admin'], ['user.User'])
        self.virus_count = kwargs['virus_count']

    def get_context(self):
        context = self.build_context()
        context['virus_count'] = self.virus_count
        return context

    def get_language(self):
        return self.admin.get_language()

    def get_template(self):
        return 'email/file_scan_found.html'

    def get_receiver(self):
        return self.admin

    def get_receiver_email(self):
        return self.admin.email

    def get_sender(self):
        return None

    def get_subject(self):
        return _("Filescan found suspicous files on %(site_url)s") % {'site_url': get_base_url()}
