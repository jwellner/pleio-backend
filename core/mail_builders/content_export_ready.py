from django.utils.translation import gettext as _

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase


def schedule_content_export_ready_mail(file_folder, owner):
    from core.models import MailInstance
    MailInstance.objects.submit(ContentExportReadyMailer, {
        'file_folder': file_folder.guid,
        'owner': owner.guid,
    })


def schedule_content_export_empty_mail(owner_guid):
    from core.models import MailInstance
    MailInstance.objects.submit(ContentExportEmptyMailer, {
        'owner': owner_guid,
    })


class ContentExportReadyMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from file.models import FileFolder
        self.file_folder: FileFolder = FileFolder.objects.get(id=kwargs['file_folder'])

        from user.models import User
        self.owner: User = User.objects.get(id=kwargs['owner'])

    def get_context(self):
        context = self.build_context(user=self.owner)
        context['download_url'] = get_full_url(self.file_folder.download_url)
        return context

    def get_language(self):
        return self.owner.get_language()

    def get_template(self):
        return 'email/content_export_ready.html'

    def get_receiver(self):
        return self.owner

    def get_receiver_email(self):
        return self.owner.email

    def get_sender(self):
        pass

    def get_subject(self):
        return _("Your content export is ready")


class ContentExportEmptyMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from user.models import User
        self.owner: User = User.objects.get(id=kwargs['owner'])

    def get_context(self):
        return self.build_context(user=self.owner)

    def get_language(self):
        return self.owner.get_language()

    def get_template(self):
        return 'email/content_export_empty.html'

    def get_receiver(self):
        return self.owner

    def get_receiver_email(self):
        return self.owner.email

    def get_sender(self):
        pass

    def get_subject(self):
        return _("Your content export is ready")
