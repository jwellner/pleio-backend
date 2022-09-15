from django.utils.translation import gettext

from core.lib import obfuscate_email, get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_group_access_request_mail(user, receiver, group):
    from core.models import MailInstance
    MailInstance.objects.submit(GroupAccessRequestMailer, {
        "user": user.guid,
        "receiver": receiver.guid,
        "group": group.guid,
    })


class GroupAccessRequestMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs.get('user'), ['user.User'])
        self.receiver = load_entity_by_id(kwargs.get('receiver'), ['user.User'])
        self.group = load_entity_by_id(kwargs.get('group'), ['core.Group'])

    def get_context(self):
        context = self.build_context(user=self.user)
        context['link'] = get_full_url(self.group.url)
        context['group_name'] = self.group.name
        context['user_obfuscated_email'] = obfuscate_email(self.user.email)
        return context

    def get_language(self):
        return self.receiver.get_language()

    def get_template(self):
        return 'email/group_access_request.html'

    def get_receiver(self):
        return self.receiver

    def get_receiver_email(self):
        return self.receiver.email

    def get_sender(self):
        return None

    def get_subject(self):
        return gettext("Access request for the %(group_name)s group") % {'group_name': self.group.name}
