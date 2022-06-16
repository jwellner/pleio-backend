# Create your tasks here
from __future__ import absolute_import, unicode_literals

import signal_disabler

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import timedelta
from django.db.models import Q, F
from django_tenants.utils import schema_context
from django.utils import timezone
from django.utils.translation import ugettext_lazy

from file.helpers.post_processing import ensure_correct_file_without_signals
from file.models import FileFolder, FILE_SCAN
from file.helpers.images import resize_and_update_image
from core.lib import get_default_email_context
from core.tasks import send_mail_multi
from file.validators import is_upload_complete
from user.models import User

logger = get_task_logger(__name__)


@shared_task(bind=True, ignore_result=True)
def resize_featured(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    '''
    Resize featured image for tenant
    '''
    with schema_context(schema_name):
        try:
            image = FileFolder.objects.get(id=file_guid)
            resize_and_update_image(image, 1200, 2000)
        except Exception as e:
            logger.error('resize_featured %s %s: %s', schema_name, file_guid, e)


@shared_task(bind=True, ignore_result=True)
def scan(self, schema_name, limit=1000):
    # pylint: disable=unused-argument
    '''
    Scan files
    '''
    with schema_context(schema_name):
        time_threshold = timezone.now() - timedelta(days=7)

        files = FileFolder.objects.filter(is_folder=False)
        files = files.filter(Q(last_scan__isnull=True) | Q(last_scan__lt=time_threshold))
        files = files.order_by(F("last_scan").desc(nulls_first=True))[:limit]

        file_count = files.count()
        virus_count = 0
        errors_count = 0
        for file in files:
            result = file.scan()
            if result == FILE_SCAN.VIRUS:
                virus_count += 1
            elif result == FILE_SCAN.UNKNOWN:
                errors_count += 1

            with signal_disabler.disable():
                file.last_scan = timezone.now()
                file.save()

        if virus_count > 0:
            context = get_default_email_context()
            subject = ugettext_lazy("Filescan found suspicous files on %(site_url)s") % {'site_url': context["site_url"]}
            context['virus_count'] = virus_count

            # mail to superadmins to notify about site access change
            for admin_user in User.objects.filter(is_superadmin=True):
                send_mail_multi.delay(
                    schema_name,
                    subject,
                    'email/file_scan_found.html',
                    context,
                    admin_user.email,
                    language=admin_user.get_language()
                )

        logger.info("Scanned %i and found %i virusses and %i errors @%s", file_count, virus_count, errors_count, schema_name)


@shared_task(autoretry_for=(AssertionError,), retry_backoff=10, max_retries=10)
def post_process_file_attributes(schema_name, instance_id):
    with schema_context(schema_name):
        instance = FileFolder.objects.get(id=instance_id)

        ensure_correct_file_without_signals(instance)

        if not is_upload_complete(instance):
            raise AssertionError(f"{instance_id}@{schema_name} still not complete.")
