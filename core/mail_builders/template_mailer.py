from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation

from core import config
from core.lib import html_to_text
from core.mail_builders.base import MailerBase


class TemplateMailerBase(MailerBase):

    def get_context(self):
        raise NotImplementedError(f"Please implement 'get_context()' for {self}")

    def get_language(self):
        raise NotImplementedError(f"Please implement 'get_language()' for {self}")

    def get_template(self):
        raise NotImplementedError(f"Please implement 'get_template()' for {self}")

    def pre_send(self, email):
        pass

    def send(self):
        self.assert_not_known_inactive_user(self.get_receiver_email())

        translation.activate(self.get_language())

        html_template = get_template(self.get_template())
        html_content = html_template.render(self.get_context())
        text_content = html_to_text(html_content)

        from_mail = formataddr((config.NAME, settings.FROM_EMAIL))

        email = EmailMultiAlternatives(subject=self.get_subject(),
                                       body=text_content,
                                       from_email=from_mail,
                                       to=[self.get_receiver_email()])
        email.attach_alternative(html_content, "text/html")

        self.pre_send(email)
        email.send()
