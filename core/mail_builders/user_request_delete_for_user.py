from django.utils.translation import gettext

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_user_request_delete_for_user_mail(user):
    from core.models import MailInstance
    MailInstance.objects.submit(UserRequestDeleteToSelfMailer,
                                mailer_kwargs={
                                    "user": user.guid,
                                })


class UserRequestDeleteToSelfMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs.get('user') else None

    def get_context(self):
        return self.build_context(user=self.user)

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return 'email/toggle_request_delete_user_requested.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return None

    def get_subject(self):
        return gettext("Request to remove account")
