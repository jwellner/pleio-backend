from django.utils.translation import gettext as _

from core.mail_builders.template_mailer import TemplateMailerBase
from user.models import User


def schedule_user_import_failed(user, stats, error_message):
    from core.models import MailInstance
    MailInstance.objects.submit(UserImportFailedMailer, {
        'user': user.guid,
        'stats': stats,
        'error_message': error_message,
    })


class UserImportFailedMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = User.objects.get(id=kwargs.get('user'))
        self.stats = kwargs['stats']
        self.error_message = kwargs['error_message']

    def get_context(self):
        context = self.build_context(user=self.user)
        context.update({
            'stats_created': self.stats.get('created', 0),
            'stats_updated': self.stats.get('updated', 0),
            'stats_error': self.stats.get('error', 0),
            'error_message': self.error_message,
        })
        return context

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return "email/user_import_failed.html"

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        pass

    def get_subject(self):
        return _("Import failed")
