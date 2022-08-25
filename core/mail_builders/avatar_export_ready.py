from django.utils.translation import gettext

from core.mail_builders.template_mailer import TemplateMailerBase
from core.models import AvatarExport


def schedule_avatar_export_ready_mail(avatar_export):
    from core.models import MailInstance
    MailInstance.objects.submit(AvatarExportReadyMailer, {
        'avatar_export': avatar_export.guid,
    })


class AvatarExportReadyMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.avatar_export: AvatarExport = AvatarExport.objects.get(pk=kwargs['avatar_export'])

    def get_context(self):
        context = self.build_context(user=self.avatar_export.initiator)
        context['download_url'] = self.avatar_export.file.download_url
        context['filename'] = self.avatar_export.file.title
        return context

    def get_language(self):
        return self.avatar_export.initiator.get_language()

    def get_template(self):
        return 'email/avatar_export_ready.html'

    def get_receiver(self):
        return self.avatar_export.initiator

    def get_receiver_email(self):
        return self.avatar_export.initiator.email

    def get_sender(self):
        return None

    def get_subject(self):
        return gettext("Avatar export is ready")
