from django.utils import translation
from django_tenants.utils import schema_context

from backend2 import celery_app as app
from celery.utils.log import get_task_logger
from core.lib import get_base_url
from event.mail_builders import QrMailer

from event.models import EventAttendee

logger = get_task_logger(__name__)


@app.task
def send_mail_with_qr_code(schema_name, attendee_id):
    '''
    send email with qr code containing url
    '''
    with schema_context(schema_name):
        attendee = EventAttendee.objects.get(id=attendee_id)
        translation.activate(attendee.language)

        try:
            mailer = QrMailer(attendee)
            mailer.send()
        except Exception as e:
            logger.error('background_email_error schema=%s site=%s to=%s event=%s type=%s error="%s"',
                         schema_name, get_base_url(), attendee.email, attendee.event.id, e.__class__, e)
