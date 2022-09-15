from django.utils.translation import gettext

from core import config
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_user_delete_complete_mail(user_info, receiver_info, to_admin, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(UserDeleteCompleteMailer,
                                mailer_kwargs={
                                    "user_info": user_info,
                                    "receiver_info": receiver_info,
                                    "to_admin": to_admin,
                                    "sender": sender.guid,
                                })


class UserDeleteCompleteMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_info = kwargs.get('user_info')
        self.receiver_info = kwargs.get('receiver_info')
        self.to_admin = bool(kwargs.get('to_admin'))
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User']) if kwargs.get('sender') else None

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['name_deleted_user'] = self.user_info['name']
        return context

    def get_language(self):
        return self.receiver_info['language']

    def get_template(self):
        return "email/admin_user_deleted.html"

    def get_receiver(self):
        from user.models import User
        return User.objects.filter(email=self.receiver_info['email']).first()

    def get_receiver_email(self):
        return self.receiver_info['email']

    def get_sender(self):
        return self.sender

    def get_subject(self):
        if self.to_admin:
            return gettext("A site administrator was removed from %(site_name)s") % {
                'site_name': config.NAME
            }
        return gettext("Account of %(name_deleted_user)s removed") % {
            'name_deleted_user': self.user_info['name']
        }
