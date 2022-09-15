from django.utils.html import format_html
from django.utils.translation import gettext

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def schedule_user_send_message_mail(message, subject, receiver, sender, copy=False):
    from core.models import MailInstance
    MailInstance.objects.submit(UserSendMessageMailer,
                                mailer_kwargs={
                                    "message": message,
                                    "subject": subject,
                                    "receiver": receiver.guid,
                                    "sender": sender.guid,
                                    "copy": copy
                                })


class UserSendMessageMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message = kwargs.get('message')
        self.subject = kwargs.get('subject')
        self.receiver = load_entity_by_id(kwargs['receiver'], ['user.User']) if kwargs.get('receiver') else None
        self.sender = load_entity_by_id(kwargs['sender'], ['user.User']) if kwargs.get('sender') else None
        self.copy = kwargs.get('copy')

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['message'] = format_html(self.message)
        context['subject'] = self.get_subject()
        return context

    def get_language(self):
        return self.receiver.get_language()

    def get_template(self):
        return "email/send_message_to_user.html"

    def get_receiver(self):
        return self.receiver

    def get_receiver_email(self):
        return self.receiver.email

    def get_sender(self):
        return self.sender

    def get_subject(self):
        if self.copy:
            return gettext("Copy: Message from {0}: {1}").format(self.sender.name, self.subject)
        return gettext("Message from {0}: {1}").format(self.sender.name, self.subject)
