import os

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.utils.translation import gettext
from django_tenants.utils import schema_context

from core.lib import datetime_format
from core.models import Attachment

logger = get_task_logger(__name__)


@shared_task(rate_limit="60/m")
def scan_attachment(schema_name, attachment_id):
    with schema_context(schema_name):
        try:
            attachment = Attachment.objects.get(id=attachment_id)

            logger.info("Scan attachment %s, last scanned %s", os.path.basename(attachment.upload.name), datetime_format(attachment.last_scan))
            attachment.last_scan = timezone.now()

            clean_file = attachment.scan()

            if not clean_file:
                attachment.blocked = True
                attachment.block_reason = gettext("This file contains a virus")
            else:
                attachment.blocked = False
                attachment.block_reason = None

            attachment.save()

            return clean_file
        except Exception as e:
            return str(e)
