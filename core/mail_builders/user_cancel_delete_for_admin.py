from django.utils.translation import gettext

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_user_cancel_delete_for_admin_mail(user, admin):
    from core.models import MailInstance
    MailInstance.objects.submit(UserCancelDeleteToAdminMailer,
                                mailer_kwargs={
                                    "user": user.guid,
                                    "admin": admin.guid
                                })


class UserCancelDeleteToAdminMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs.get('user') else None
        self.admin = load_entity_by_id(kwargs['admin'], ['user.User']) if kwargs.get('admin') else None

    def get_context(self):
        return self.build_context(user=self.user)

    def get_language(self):
        return self.admin.get_language()

    def get_template(self):
        return 'email/toggle_request_delete_user_cancelled_admin.html'

    def get_receiver(self):
        return self.admin

    def get_receiver_email(self):
        return self.admin.email

    def get_sender(self):
        return self.user

    def get_subject(self):
        return gettext("Request to remove account cancelled")
