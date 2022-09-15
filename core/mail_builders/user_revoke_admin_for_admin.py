from django.utils.translation import gettext

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_revoke_admin_for_admin_mail(user, admin, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(UserRevokeAdminForAdminMailer,
                                mailer_kwargs={
                                    "user": user.guid,
                                    "admin": admin.guid,
                                    "sender": sender.guid,
                                })


class UserRevokeAdminForAdminMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs.get('user') else None
        self.admin = load_entity_by_id(kwargs['admin'], ['user.User']) if kwargs.get('admin') else None
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User']) if kwargs.get('sender') else None

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['name_of_user_admin_role_changed'] = self.user.name
        context['link'] = get_full_url(self.user.url)
        return context

    def get_language(self):
        return self.admin.get_language()

    def get_template(self):
        return "email/user_role_admin_removed_for_admins.html"

    def get_receiver(self):
        return self.admin

    def get_receiver_email(self):
        return self.admin.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return gettext("A site administrator was removed from %(site_name)s") % {'site_name': config.NAME}
