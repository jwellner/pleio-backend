from django.utils.translation import gettext as _

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase


def submit_group_membership_approved_mail(group, user):
    from core.models import MailInstance
    MailInstance.objects.submit(GroupMembershipApprovedMailer,
                                mailer_kwargs={
                                    'group': group.guid,
                                    'user': user.guid,
                                })


class GroupMembershipApprovedMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        from core.models import Group
        from user.models import User
        self.group: Group = Group.objects.get(pk=kwargs['group'])
        self.user: User = User.objects.get(pk=kwargs['user'])
        super().__init__(**kwargs)

    def get_context(self):
        context = self.build_context(user=self.user)
        context['group_name'] = self.group.name
        context['link'] = get_full_url(self.group.url)
        return context

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return 'email/accept_membership_request.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        return None

    def get_subject(self):
        return _("Request for access to the %(group_name)s group has been approved") % {'group_name': self.group.name}
