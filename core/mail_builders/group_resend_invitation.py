from django.utils.translation import gettext

from core import config
from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_resend_group_invitation_mail(invitation, sender):
    from core.models import MailInstance
    MailInstance.objects.submit(ResendGroupInvitationMailer,
                                mailer_kwargs={
                                    'invitation': invitation.id,
                                    'sender': sender.guid
                                })


class ResendGroupInvitationMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])
        self.invitation = load_entity_by_id(kwargs['invitation'], ['core.GroupInvitation'])

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['link'] = get_full_url('/groups/invitations/?invitecode={}'.format(self.invitation.code))
        context['group_name'] = self.invitation.group.name
        return context

    def get_language(self):
        if self.invitation.invited_user:
            return self.invitation.invited_user.get_language()
        return config.LANGUAGE

    def get_template(self):
        return 'email/resend_group_invitation.html'

    def get_receiver(self):
        return self.invitation.invited_user

    def get_receiver_email(self):
        if self.invitation.invited_user:
            return self.invitation.invited_user.email
        return self.invitation.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        return gettext("Reminder to become a member of the %(group_name)s group") % {'group_name': self.invitation.group.name}
