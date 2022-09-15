from django.utils.translation import gettext

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_revoke_admin_for_user_mail(user, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(UserRevokeAdminForSelfMailer,
                                mailer_kwargs={
                                    "user": user.guid,
                                    "sender": sender.guid,
                                })


class UserRevokeAdminForSelfMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs.get('user') else None
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User']) if kwargs.get('sender') else None

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['name_of_user_admin_role_changed'] = self.user.name
        context['link'] = get_full_url(self.user.url)
        return context

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return "email/user_role_admin_removed_for_user.html"

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return gettext("Your site administrator rights for %(site_name)s were removed") % {'site_name': config.NAME}
