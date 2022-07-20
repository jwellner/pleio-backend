from django.utils.html import format_html
from django.utils.translation import ugettext as _

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from event.models import Event
from user.models import User


def submit_send_event_message(kwargs, delay=True):
    from core.models import MailInstance
    MailInstance.objects.submit(CustomMessageMailer,
                                mailer_kwargs=kwargs,
                                delay=delay)


class CustomMessageMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super(CustomMessageMailer, self).__init__(**kwargs)
        self.event = Event.objects.get(pk=kwargs['event'])
        self.sender = User.objects.get(pk=kwargs['sender'])
        self.message = kwargs['message']
        self.subject = kwargs['subject']
        self.mail_info = kwargs['mail_info']
        self.copy = kwargs.get('copy', False)

    def get_receiver(self):
        return User.objects.filter(email=self.mail_info['email']).first()

    def get_receiver_email(self):
        return self.mail_info['email']

    def get_sender(self):
        return self.sender

    def get_subject(self):
        if self.copy:
            return _("Copy: Message from event {0}: {1}").format(self.event.title, self.subject)
        return _("Message from event {0}: {1}").format(self.event.title, self.subject)

    def get_template(self):
        return 'email/send_message_to_event.html'

    def get_context(self):
        context = self.build_context(user=self.sender)
        context['message'] = format_html(self.message)
        context['event'] = self.event.title
        context['event_url'] = get_full_url(self.event.url)
        return context

    def get_language(self):
        return self.mail_info['language']
