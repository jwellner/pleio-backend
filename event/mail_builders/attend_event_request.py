from django.utils.translation import gettext as _

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def submit_attend_event_wa_request(kwargs):
    from core.models import MailInstance
    MailInstance.objects.submit(AttendWithoutAccountMailer, mailer_kwargs=kwargs)


class AttendWithoutAccountMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super(AttendWithoutAccountMailer, self).__init__(**kwargs)
        self.event = load_entity_by_id(self.kwargs['event'], ['event.Event'])
        self.email = self.kwargs['email']
        self.language = self.kwargs['language']
        self.link = self.kwargs['link']

    def get_subject(self):
        return _("Confirmation of registration %s") % self.event.title

    def get_receiver_email(self):
        return self.email

    def get_language(self):
        return self.kwargs['language']

    def get_template(self):
        return 'email/attend_event_without_account.html'

    def get_context(self):
        context = self.build_context()
        context['link'] = self.link
        context['title'] = self.event.title

        context['location'] = self.event.location
        context['locationLink'] = self.event.location_link
        context['locationAddress'] = self.event.location_address

        context['start_date'] = self.event.start_date

        return context

    def get_sender(self):
        return None

    def get_receiver(self):
        return None
