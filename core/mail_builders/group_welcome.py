from django.utils.translation import gettext as _

from core.lib import html_to_text, get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_group_welcome_mail(user, group):
    from core.models import MailInstance
    MailInstance.objects.submit(GroupWelcomeMailer,
                                mailer_kwargs={
                                    'group': group.guid,
                                    'user': user.guid,
                                })


class GroupWelcomeMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.group = load_entity_by_id(kwargs['group'], ['core.Group'])
        self.user = load_entity_by_id(kwargs['user'], ['user.User'])

    def get_context(self):
        if not self.group.welcome_message:
            raise self.FailSilentlyError()

        context = self.build_context(user=self.user)
        context['welcome_message'] = self._get_message()
        context['welcome_message'] = context['welcome_message'].replace("[name]", self.user.name)
        context['welcome_message'] = context['welcome_message'].replace("[group_name]", self.group.name)
        context['welcome_message'] = context['welcome_message'].replace("[group_url]", get_full_url(self.group.url))

        return context

    def _get_message(self):
        has_message = html_to_text(self.group.welcome_message)
        return has_message.strip() if has_message else None

    def get_language(self):
        return self.user.get_language()

    def get_template(self):
        return 'email/group_welcome.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.user.email

    def get_sender(self):
        pass

    def get_subject(self):
        return _("Welcome to %(group_name)s") % {'group_name': self.group.name}
