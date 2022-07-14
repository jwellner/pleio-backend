from core.lib import get_full_url

from django.utils.translation import gettext as _

from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def submit_mail_at_accept_from_waitinglist(**kwargs):
    from core.models import MailInstance
    MailInstance.objects.submit(FromWaitinglistToAccept, mailer_kwargs=kwargs)


class FromWaitinglistToAccept(TemplateMailerBase):

    def __init__(self, **kwargs):
        super(FromWaitinglistToAccept, self).__init__(**kwargs)
        self.event = load_entity_by_id(self.kwargs['event'], ['event.Event'])
        self.attendee = load_entity_by_id(self.kwargs['attendee'], ['event.EventAttendee'])

    def get_subject(self):
        return _("Added to event %s from waitinglist") % self.event.title

    def get_sender(self):
        return None

    def get_receiver(self):
        return self.attendee.user

    def get_receiver_email(self):
        return self.attendee.email

    def get_template(self):
        return 'email/attend_event_from_waitinglist.html'

    def get_context(self):
        context = self.build_context(mail_info=self.attendee.as_mailinfo())
        context['link'] = get_full_url(self.event.url)
        context['title'] = self.event.title

        context['location'] = self.event.location
        context['locationLink'] = self.event.location_link
        context['locationAddress'] = self.event.location_address

        context['start_date'] = self.event.start_date
        return context

    def get_language(self):
        return self.attendee.language
