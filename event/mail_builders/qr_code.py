from email.mime.image import MIMEImage
from email.utils import formataddr
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils.text import slugify
from django.utils.translation import gettext as _

from core import config
from core.lib import get_full_url, get_default_email_context, html_to_text, generate_code
from core.mail_builders.base import MailerBase
from event.lib import get_url
from event.models import EventAttendee


class QrMailer(MailerBase):
    _html = None
    _filename = None

    def __init__(self, attendee: EventAttendee):
        self.attendee = attendee

    @property
    def code(self):
        if not self.attendee.code:
            self.attendee.code = generate_code()
            self.attendee.save()
        return self.attendee.code

    @property
    def filename(self):
        if not self._filename:
            if hasattr(self.attendee.event, 'title') and self.attendee.event.title:
                file_name = slugify(self.attendee.event.title)[:238].removesuffix("-")
            else:
                file_name = self.attendee.event.id
            self._filename = f"qr_access_{file_name}.png"
        return self._filename

    @property
    def subject(self):
        return _("QR code for %s") % self.attendee.event.title

    @property
    def attachment(self):
        qr_code = qrcode.make(get_full_url(f"/events/view/guest-list?code={self.code}"))
        stream = BytesIO()
        qr_code.save(stream, format="png")
        stream.seek(0)
        img_obj = stream.read()
        code_image = MIMEImage(img_obj, name=self.filename, _subtype='png')
        code_image.add_header('Content-Disposition', f'attachment; filename="{self.filename}"')
        code_image.add_header('Content-ID', self.filename)
        return code_image

    @property
    def html_content(self):
        if not self._html:
            context = get_default_email_context(self.attendee.user)
            context['title'] = self.attendee.event.title
            context['location'] = self.attendee.event.location
            context['locationAddress'] = self.attendee.event.location_address
            context['locationLink'] = self.attendee.event.location_link
            context['startDate'] = self.attendee.event.start_date
            context['link'] = get_url(self.attendee.event)
            context['qr_filename'] = f"cid:{self.filename}"

            html_template = get_template('email/attend_event_with_qr_access.html')
            self._html = html_template.render(context)
        return self._html

    @property
    def from_email(self):
        return formataddr((config.NAME, settings.FROM_EMAIL))

    @property
    def reply_to(self):
        return None

    @property
    def to(self):
        return [self.attendee.email]

    @property
    def text_content(self):
        return html_to_text(self.html_content)

    def send(self):
        if self.ignore_email(self.attendee.email):
            return

        email = EmailMultiAlternatives(subject=self.subject,
                                       body=self.text_content,
                                       from_email=self.from_email,
                                       to=self.to,
                                       reply_to=self.reply_to)
        email.attach_alternative(self.html_content, "text/html")
        email.attach(self.attachment)
        email.send()