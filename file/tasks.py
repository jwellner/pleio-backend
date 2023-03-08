from __future__ import absolute_import, unicode_literals

import math
import os
from os.path import exists

from celery import shared_task, chord
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils.translation import gettext
from django_tenants.utils import schema_context
from django.utils import timezone

from core.lib import datetime_format
from core.models import Attachment
from file.helpers.post_processing import ensure_correct_file_without_signals
from file.mail_builders.file_scan_found import schedule_file_scan_found_mail
from file.models import FileFolder, ScanIncident
from file.helpers.images import resize_and_update_image
from file.validators import is_upload_complete
from user.models import User

logger = get_task_logger(__name__)


@shared_task
def resize_featured(schema_name, file_guid):
    '''
    Resize featured image for tenant
    '''
    with schema_context(schema_name):
        try:
            image = FileFolder.objects.get(id=file_guid)
            resize_and_update_image(image, 1200, 2000)
        except Exception as e:
            logger.error('resize_featured %s %s: %s', schema_name, file_guid, e)


@shared_task
def schedule_scan_finished(schema_name):
    with schema_context(schema_name):
        incidents = ScanIncident.objects.filter(file_created__gte=timezone.now() - timezone.timedelta(days=1))

        virus_count = incidents.filter(is_virus=True).count()
        error_count = incidents.filter(is_virus=False).count()

        if incidents.count():
            for admin_user in User.objects.filter(is_superadmin=True):
                schedule_file_scan_found_mail(virus_count=virus_count,
                                              error_count=error_count,
                                              admin=admin_user)

        logger.info("Scanned found %i virusses @%s", incidents, schema_name)


@shared_task
def schedule_scan(schema_name):
    with schema_context(schema_name):
        runner = ScheduleScan()
        runner.run(schema_name)


class ScheduleScan:

    def file_limit(self):
        return math.ceil(self.file_queryset().count() / settings.SCAN_CYCLE_DAYS)

    def attachment_limit(self):
        return math.ceil(self.attachment_queryset().count() / settings.SCAN_CYCLE_DAYS)

    @staticmethod
    def file_queryset():
        return FileFolder.objects.filter_files()

    def collect_files(self):
        return self.file_queryset().order_by('last_scan').values_list('id', flat=True)[:self.file_limit()]

    @staticmethod
    def attachment_queryset():
        return Attachment.objects.all()

    def collect_attachments(self):
        return self.attachment_queryset().order_by('last_scan').values_list('id', flat=True)[:self.attachment_limit()]

    def generate_tasks(self, schema_name):
        from core.tasks import scan_attachment
        for file_id in self.collect_files():
            yield scan_file.si(schema_name, str(file_id))
        for file_id in self.collect_attachments():
            yield scan_attachment.si(schema_name, str(file_id))

    def run(self, schema_name):
        chord([*self.generate_tasks(schema_name)],
              schedule_scan_finished.si(schema_name)).apply_async()


@shared_task(rate_limit="60/m")
def scan_file(schema_name, file_id):
    try:
        with schema_context(schema_name):
            file = FileFolder.objects.filter(id=file_id).first()
            if not file or not file.is_file():
                return

            if not file.upload.name or not exists(file.upload.path):
                file.blocked = True
                file.block_reason = gettext("File not found on file storage")
                file.save()
                return

            logger.info("Scan file %s, last scanned %s", os.path.basename(file.upload.name), datetime_format(file.last_scan))
            file.last_scan = timezone.now()

            result = file.scan()
            if not result:
                file.blocked = True
                file.block_reason = gettext("This file contains a virus")
            else:
                file.blocked = False
                file.block_reason = None
            file.save()

            return result
    except Exception as e:
        # Make sure the task exits OK.
        return str(e)


@shared_task(autoretry_for=(AssertionError,), retry_backoff=10, max_retries=10)
def post_process_file_attributes(schema_name, instance_id):
    with schema_context(schema_name):
        instance = FileFolder.objects.get(id=instance_id)

        ensure_correct_file_without_signals(instance)

        if not is_upload_complete(instance):
            raise AssertionError(f"{instance_id}@{schema_name} still not complete.")
