from __future__ import absolute_import, unicode_literals

import math
import os
from os.path import exists

from celery import shared_task, chord, signature, chain, group
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils.translation import gettext
from django_tenants.utils import schema_context
from django.utils import timezone

from control.models import FileOperationLog
from core.lib import datetime_format
from file.helpers.post_processing import ensure_correct_file_without_signals
from file.mail_builders.file_scan_found import schedule_file_scan_found_mail
from file.models import FileFolder, ScanIncident
from file.helpers.images import resize_and_update_image
from file.validators import is_upload_complete
from tenants.models import Client
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

        logger.info("Scanned found %i incidents @%s", incidents.count(), schema_name)


@shared_task
def schedule_scan_all_tenants():
    tasks = []
    for tenant in Client.objects.exclude(schema_name='public'):
        tasks.append(signature(schedule_scan, kwargs={'schema_name': tenant.schema_name}))
    chain(*tasks).apply_async()


@shared_task
def schedule_scan(result=None, schema_name=None):
    with schema_context(schema_name):
        runner = ScheduleScan(schema_name=schema_name,
                              file_offset=result or 10)
        return runner.run()


class ScheduleScan:

    def __init__(self, schema_name, file_offset):
        self.schema_name = schema_name
        self.file_offset = file_offset

    def file_limit(self):
        return math.ceil(self.file_queryset().count() / int(settings.SCAN_CYCLE_DAYS))

    @staticmethod
    def file_queryset():
        return FileFolder.objects.filter_files()

    def collect_files(self):
        return self.file_queryset().order_by('last_scan').values_list('id', flat=True)[:self.file_limit()]

    def generate_tasks(self):
        reference = timezone.now()
        for count_down, file_id in enumerate([*self.collect_files()]):
            offset_seconds = self.file_offset + count_down
            yield signature(scan_file, args=(self.schema_name, str(file_id)), eta=(reference+timezone.timedelta(seconds=offset_seconds)))

    def run(self):
        tasks = [*self.generate_tasks()]
        chord(tasks, schedule_scan_finished.si(self.schema_name)).apply_async()
        FileOperationLog.objects.add_log("file.tasks.ScheduleScan", {
            "file_offset": self.file_offset,
            "selected_files": len(tasks),
            "all_files": self.file_queryset().count(),
        })
        return len(tasks) + self.file_offset


@shared_task(rate_limit="30/m")
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

            logger.info("At %s Scan file %s, last scanned %s", schema_name, os.path.basename(file.upload.name), datetime_format(file.last_scan))
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
