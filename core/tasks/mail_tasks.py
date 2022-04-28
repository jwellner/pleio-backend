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
from user.models import User
import qrcode
from io import BytesIO
from email.mime.image import MIMEImage

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


@shared_task(bind=True, ignore_result=True)
def send_mail_multi_with_qr_code(self, schema_name, subject, html_template, context, email_address, file_name,  url, reply_to=None, language=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    '''
    send email with qr code containing url
    '''
    with schema_context(schema_name):
        translation.activate(language or config.LANGUAGE)

        if User.objects.filter(is_active=False, email=email_address).first():
            # User not found
            return

        html_template = get_template(html_template)
        html_content = html_template.render(context)
        text_content = html_to_text(html_content)

        from_mail = formataddr((config.NAME, settings.FROM_EMAIL))

        qr_code = qrcode.make(url)
        stream = BytesIO()
        qr_code.save(stream, format="png")
        stream.seek(0)
        img_obj=stream.read()
        code_image = MIMEImage(img_obj, name = file_name, _subtype = 'png')
        code_image.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
        email = EmailMultiAlternatives(subject, text_content, from_mail, to=[email_address], reply_to=reply_to)
        email.attach_alternative(html_content, "text/html")
        email.attach(code_image)

        try:
            email.send()
        except Exception as e:
            logger.error('email sent to %s failed. Error: %s', email_address, e)
            raise e
