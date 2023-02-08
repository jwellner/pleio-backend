from django.utils.translation import gettext

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.convert import filter_html_mail_input
from core.utils.entity import load_entity_by_id


def schedule_group_message_mail(message, subject, receiver, group, sender, copy):
    from core.models import MailInstance
    MailInstance.objects.submit(SendGroupMessageMailer,
                                mailer_kwargs={
                                    'message': message,
                                    'subject': subject,
                                    'receiver': receiver.guid,
                                    'sender': sender.guid,
                                    'group': group.guid,
                                    'copy': copy,
                                })


class SendGroupMessageMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message = kwargs.get('message')
        self.subject = kwargs.get('subject')
        self.receiver = load_entity_by_id(kwargs['receiver'], ['user.User'])
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User'])
        self.group = load_entity_by_id(kwargs['group'], ['core.Group'])
        self.copy = bool(kwargs.get('copy'))

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['message'] = filter_html_mail_input(self.message)
        context['group'] = self.group.name
        context['group_url'] = get_full_url(self.group.url)
        return context

    def get_language(self):
        return self.receiver.get_language()

    def get_template(self):
        return 'email/send_message_to_group.html'

    def get_receiver(self):
        return self.receiver

    def get_receiver_email(self):
        return self.receiver.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        if self.copy:
            return gettext("Copy: Message from group {0}: {1}").format(self.group.name, self.subject)
        return gettext("Message from group {0}: {1}").format(self.group.name, self.subject)
