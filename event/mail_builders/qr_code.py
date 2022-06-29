from email.mime.image import MIMEImage
from io import BytesIO

import qrcode
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext as _

from core.lib import get_full_url, generate_code
from core.mail_builders.template_mailer import TemplateMailerBase
from event.lib import get_url


class QrMailer(TemplateMailerBase):
    _html = None
    _filename = None

    def __init__(self, attendee):
        from event.models import EventAttendee
        self.attendee = EventAttendee.objects.get(id=attendee)
        self.content_id = get_random_string(length=32)

    def get_code(self):
        if not self.attendee.code:
            self.attendee.code = generate_code()
            self.attendee.save()
        return self.attendee.code

    def get_filename(self):
        if self.attendee.event.title:
            file_name = slugify(self.attendee.event.title)[:238].removesuffix("-")
        else:
            file_name = self.attendee.event.id
        return f"qr_access_{file_name}.png"

    def get_subject(self):
        return _("QR code for %s") % self.attendee.event.title

    def get_qr_code_url(self):
        return get_full_url(f"/events/view/guest-list?code={self.get_code()}")

    def get_receiver_email(self):
        return self.attendee.email

    def get_receiver(self):
        return self.attendee.user

    def get_sender(self):
        return None

    def get_context(self):
        context = self.build_context(user=self.attendee.user)
        context['title'] = self.attendee.event.title
        context['location'] = self.attendee.event.location
        context['locationAddress'] = self.attendee.event.location_address
        context['locationLink'] = self.attendee.event.location_link
        context['startDate'] = self.attendee.event.start_date
        context['link'] = get_url(self.attendee.event)
        context['qr_filename'] = f"cid:{self.content_id}"
        return context

    def get_template(self):
        return 'email/attend_event_with_qr_access.html'

    def get_language(self):
        return self.attendee.language

    def pre_send(self, email):
        email.attach(self.get_attachment())

    def get_attachment(self):
        stream = BytesIO()
        qr_code = qrcode.make(self.get_qr_code_url())
        qr_code.save(stream, format="png")

        stream.seek(0)
        img_obj = stream.read()
        filename = self.get_filename()
        code_image = MIMEImage(img_obj, name=filename, _subtype='png')
        code_image.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        code_image.add_header('Content-ID', self.content_id)
        return code_image


def send_event_qr(attendee):
    from core.models import MailInstance
    MailInstance.objects.submit(QrMailer, mailer_kwargs={
        'attendee': attendee.id
    })
