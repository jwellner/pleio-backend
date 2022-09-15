from django.utils.translation import gettext

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_reject_membership_mail(user, receiver, group):
    from core.models import MailInstance
    MailInstance.objects.submit(RejectGroupMembershipMailer,
                                mailer_kwargs={
                                    'group': group.guid,
                                    'user': user.guid,
                                    'receiver': receiver.guid
                                })


class RejectGroupMembershipMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = load_entity_by_id(kwargs['user'], ['user.User'])
        self.receiver = load_entity_by_id(kwargs['receiver'], ['user.User'])
        self.group = load_entity_by_id(kwargs['group'], ['core.Group'])

    def get_context(self):
        context = self.build_context(user=self.user)
        context['group_name'] = self.group.name
        return context

    def get_language(self):
        return self.receiver.get_language()

    def get_template(self):
        return "email/reject_membership_request.html"

    def get_receiver(self):
        return self.receiver

    def get_receiver_email(self):
        return self.receiver.email

    def get_sender(self):
        return self.user

    def get_subject(self):
        return gettext("Request for access to the %(group_name)s group has been refused") % {
            'group_name': self.group.name
        }
