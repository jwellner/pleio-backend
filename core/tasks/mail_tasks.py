from celery import shared_task
from celery.utils.log import get_task_logger
from django_tenants.utils import schema_context

from core.mail_builders.base import MailerBase

logger = get_task_logger(__name__)


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
