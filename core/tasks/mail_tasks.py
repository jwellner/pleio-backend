from celery import shared_task
from celery.utils.log import get_task_logger
from core import config
from core.lib import html_to_text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import translation
from django.template.loader import get_template
from django_tenants.utils import schema_context
from email.utils import formataddr

from core.mail_builders.base import MailerBase
from user.models import User

logger = get_task_logger(__name__)


@shared_task(bind=True, ignore_result=True)
def send_mail_multi(self, schema_name, subject, html_template, context, email_address, reply_to=None, language=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    '''
    send email
    '''
    with schema_context(schema_name):
        translation.activate(language or config.LANGUAGE)

        if not User.objects.filter(is_active=False, email=email_address).first():
            html_template = get_template(html_template)
            html_content = html_template.render(context)
            text_content = html_to_text(html_content)

            from_mail = formataddr((config.NAME, settings.FROM_EMAIL))

            try:
                email = EmailMultiAlternatives(subject, text_content, from_mail, to=[email_address], reply_to=reply_to)
                email.attach_alternative(html_content, "text/html")
                email.send()
            except Exception as e:
                logger.error('email sent to %s failed. Error: %s', email_address, e)


@shared_task(ignore_result=True)
def send_mail_by_instance(schema_name, instance_id):
    from core.models.mail import load_mailinstance

    with schema_context(schema_name):
        try:
            instance = load_mailinstance(instance_id)
            instance.send()

            if instance.error:
                logger.error("background_email_error: id=%s schema=%s error=%s message=%s",
                             instance_id, schema_name, instance.error.__class__, str(instance.error))
        except MailerBase.FailSilentlyError:
            pass
