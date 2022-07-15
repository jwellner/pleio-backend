from django.core import signing
from django.utils.module_loading import import_string

from core import config


class MailerBase:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def send(self):
        raise NotImplementedError(f"Please implement 'send()' for {self.__class__}")

    def get_receiver(self):
        raise NotImplementedError(f"Please implement 'get_receiver()' for {self.__class__}")

    def get_receiver_email(self):
        raise NotImplementedError(f"Please implement 'get_receiver_email()' for {self.__class__}")

    def get_sender(self):
        raise NotImplementedError(f"Please implement 'get_sender()' for {self.__class__}")

    def get_subject(self):
        raise NotImplementedError(f"Please implement 'get_subject()' for {self.__class__}")

    def build_context(self, mail_info=None, user=None):
        from core.lib import get_base_url, get_full_url
        context = {
            'site_url': get_base_url(),
            'site_name': config.NAME,
            'primary_color': config.COLOR_PRIMARY,
            'header_color': config.COLOR_HEADER if config.COLOR_HEADER else config.COLOR_PRIMARY,
        }
        if user:
            mail_info = user.as_mailinfo()
            signer = signing.TimestampSigner()
            token = signer.sign_object({
                "id": str(user.id),
                "email": user.email
            })
            context['unsubscribe_url'] = get_full_url('/edit_email_settings/' + token)
            context['user_url'] = get_full_url(user.url)
        if mail_info:
            context['user_name'] = mail_info['name']
        return context

    class FailSilentlyError(Exception):
        pass

    class IgnoreInactiveUserMailError(FailSilentlyError):
        pass

    @staticmethod
    def assert_not_known_inactive_user(email):
        """ Test if the user is not known to be inactive. """
        from user.models import User
        if User.objects.filter(is_active=False, email=email).exists():
            raise MailerBase.IgnoreInactiveUserMailError(f"Did not send mail to {email}")
        return True

    @classmethod
    def class_id(cls):
        return f"{cls.__module__}.{cls.__qualname__}"


def assert_valid_mailer_subclass(mailer):
    if isinstance(mailer, str):
        mailer_class = import_string(mailer)
    else:
        mailer_class = mailer
    assert issubclass(mailer_class, MailerBase), f"{mailer_class} is not a subclass of core.mail_builders.base.MailerBase"
