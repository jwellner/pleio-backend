from django.utils.translation import gettext_lazy as _

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def submit_attend_event_wa_confirm(attendee_id, code):
    from core.models import MailInstance
    MailInstance.objects.submit(AttendEventWithoutAccountConfirmMailer,
                                mailer_kwargs={'attendee': attendee_id,
                                               'code': code})


class AttendEventWithoutAccountConfirmMailer(TemplateMailerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attendee = load_entity_by_id(self.kwargs['attendee'], ['event.EventAttendee'])
        self.event = self.attendee.event
        self.code = self.kwargs['code']

    def get_context(self):
        context = self.build_context()

        leave_url = LeaveUrl(self.event)
        leave_url.add_email(self.attendee.email)
        leave_url.add_code(self.code)

        context['link'] = get_full_url(self.event.url)
        context['leave_link'] = get_full_url(leave_url.get_url())
        context['title'] = self.event.title

        context['location'] = self.event.location
        context['locationLink'] = self.event.location_link
        context['locationAddress'] = self.event.location_address

        context['start_date'] = self.event.start_date
        context['state'] = self.attendee.state

        return context

    def get_language(self):
        return self.attendee.language

    def get_template(self):
        return 'email/attend_event_without_account_confirm.html'

    def get_receiver(self):
        return None

    def get_receiver_email(self):
        return self.attendee.email

    def get_sender(self):
        return None

    def get_subject(self):
        return _("Confirmation of registration for %s") % self.event.title


class LeaveUrl:

    def __init__(self, event):
        self.url = '/events/confirm/' + event.guid + '?delete=true'

    def add_email(self, email):
        self.url = self.url + '&email=' + email
        return self

    def add_code(self, code):
        self.url = self.url + '&code=' + code
        return self

    def get_url(self):
        return self.url
