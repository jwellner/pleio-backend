import io
from email.mime.text import MIMEText

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.convert import tiptap_to_html, tiptap_to_text
from core.utils.entity import load_entity_by_id
from event.models import EventAttendee


def send_mail(attendee):
    from core.models import MailInstance
    MailInstance.objects.submit(AttendeeWelcomeMailMailer,
                                mailer_kwargs={'attendee': attendee.pk},
                                delay=False)


class AttendeeWelcomeMailMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attendee: EventAttendee = load_entity_by_id(kwargs['attendee'], [EventAttendee])

    def get_context(self):
        context = self.build_context(self.attendee.as_mailinfo())
        context['message'] = self._replace_wildcards(self.attendee.event.attendee_welcome_mail_content)
        context['subject'] = self.attendee.event.title
        context['location'] = self.attendee.event.location
        context['locationLink'] = self.attendee.event.location_link
        context['locationAddress'] = self.attendee.event.location_address
        context['start_date'] = self.attendee.event.start_date
        return context

    def _replace_wildcards(self, message):
        message = tiptap_to_html(message)
        message = message.replace("[name]", self.attendee.name)
        return message

    def get_language(self):
        return self.attendee.language

    def get_template(self):
        return "email/send_attendee_welcome_mail.html"

    def get_receiver(self):
        return self.attendee.user

    def get_receiver_email(self):
        return self.attendee.email

    def get_sender(self):
        return None

    def get_subject(self):
        return self.attendee.event.attendee_welcome_mail_subject

    def pre_send(self, email):
        email.attach(self.get_attachment())

    def get_attachment(self):
        stream = io.StringIO()
        stream.write('BEGIN:VCALENDAR\n')
        stream.write('VERSION:2.0\n')
        stream.write('BEGIN:VEVENT\n')

        fmt = "%Y%m%dT%H%M%S"
        stream.write('DTSTART:%sZ\n' % self.attendee.event.start_date.strftime(fmt))
        stream.write('DTEND:%sZ\n' % self.attendee.event.end_date.strftime(fmt))

        stream.write('SUMMARY:%s\n' % self.attendee.event.title)
        if self.attendee.event.abstract:
            stream.write('DESCRIPTION:%s\n' % tiptap_to_text(self.attendee.event.rich_description))
        if self.attendee.event.location:
            stream.write('LOCATION:%s\n' % self.attendee.event.location)
        elif self.attendee.event.location_address:
            stream.write('LOCATION:%s\n' % self.attendee.event.location_address)
        stream.write('URL:%s\n' % get_full_url(self.attendee.event.url))
        stream.write('END:VEVENT\n')
        stream.write('END:VCALENDAR\n')

        stream.seek(0)
        img_obj = stream.read()
        ical_data = MIMEText(img_obj, _subtype='calendar; method="REQUEST"')
        ical_data.add_header('Content-Disposition', f'attachment; filename="{self.attendee.event.slug}.ics"')
        return ical_data
