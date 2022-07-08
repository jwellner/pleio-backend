import requests

import celery
from auditlog.models import LogEntry
from celery import shared_task
from celery.utils.log import get_task_logger
from core import config
from core.models import SiteStat, Attachment, ResizedImage, Entity
from core.tasks.notification_tasks import create_notifications_for_scheduled_content
from django.conf import settings
from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Sum
from django_tenants.utils import schema_context
from django.utils import timezone
from datetime import timedelta

from file.models import FileFolder
from tenants.models import Client
from user.models import User

logger = get_task_logger(__name__)


@shared_task
def dispatch_crons(period):
    '''
    Dispatch period cron tasks for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Schedule cron %s for %s', period, client.schema_name)

        if period == 'hourly':
            create_notifications_for_scheduled_content.delay(client.schema_name)
            send_notifications.delay(client.schema_name)
            depublicate_content.delay(client.schema_name)

        if period == 'daily':
            save_db_disk_usage.delay(client.schema_name)
            save_file_disk_usage.delay(client.schema_name)
            ban_users_that_bounce.delay(client.schema_name)
            ban_users_with_no_account.delay(client.schema_name)
            resize_pending_images.delay(client.schema_name)
            cleanup_auditlog.delay(client.schema_name)

        if period == 'weekly':
            remove_floating_attachments.delay(client.schema_name)

        if period in ['daily', 'weekly', 'monthly']:
            send_overview.delay(client.schema_name, period)


@shared_task(bind=True)
def dispatch_task(self, task, *kwargs):
    '''
    Dispatch task for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Dispatch task %s for %s', task, client.schema_name)
        self.app.tasks[task].delay(client.schema_name, *kwargs)


@shared_task
def send_notifications(schema_name):
    '''
    Send notification mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_notification_emails', '--schema', schema_name])


@shared_task
def send_overview(schema_name, period):
    '''
    Send overview mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_overview_emails', '--schema', schema_name, '--interval', period])


@shared_task
def save_db_disk_usage(schema_name):
    '''
    Save size by schema_name
    '''
    cursor = connection.cursor()
    cursor.execute(f"SELECT sum(pg_relation_size(schemaname || '.' || tablename))::bigint FROM pg_tables WHERE schemaname = '{schema_name}';")
    result = cursor.fetchone()
    size_in_bytes = result[0]

    with schema_context(schema_name):
        SiteStat.objects.create(
            stat_type='DB_SIZE',
            value=size_in_bytes
        )


@shared_task
def save_file_disk_usage(schema_name):
    '''
    Save size by schema_name
    '''
    total_size = 0
    with schema_context(schema_name):
        logger.info('get_file_size \'%s\'', schema_name)

        file_folder_size = 0
        attachment_size = 0

        f = FileFolder.objects.filter(is_folder=False).aggregate(total_size=Sum('size'))
        if f.get('total_size', 0):
            file_folder_size = f.get('total_size', 0)

        e = Attachment.objects.all().aggregate(total_size=Sum('size'))
        if e.get('total_size', 0):
            attachment_size = e.get('total_size', 0)

        total_size = file_folder_size + attachment_size

        SiteStat.objects.create(
            stat_type='DISK_SIZE',
            value=total_size
        )


@shared_task
def ban_users_that_bounce(schema_name):
    '''
    Ban users with email adresses that bounce
    '''
    with schema_context(schema_name):
        if not settings.BOUNCER_URL or not settings.BOUNCER_TOKEN:
            logger.error("Could not process bouncing emails as bouncer_url or bouncer_token is not set")
            return

        try:
            headers = {
                'Authorization': 'Token ' + settings.BOUNCER_TOKEN,
                'Accept': 'application/json'
            }
            last_received = config.LAST_RECEIVED_BOUNCING_EMAIL
            url = settings.BOUNCER_URL + '/api/orphans?last_received__gt=' + last_received
            r = requests.get(url, headers=headers)
        except Exception as e:
            logger.error("Error getting bouncing email adresses: %s", e)

        count = 0
        for orphan in r.json():
            last_received = orphan['last_received']

            try:
                user = User.objects.get(email=orphan['email'])
            except ObjectDoesNotExist:
                continue

            if not user.is_active:
                continue

            user.is_active = False
            user.ban_reason = 'bouncing email adres'
            user.save()
            count = count + 1

        if count:
            logger.info("Accounts blocked beacause of boucning email: %s", count)
        config.LAST_RECEIVED_BOUNCING_EMAIL = last_received


@shared_task
def ban_users_with_no_account(schema_name):
    '''
    Ban users with email adresses that bounce
    '''
    with schema_context(schema_name):
        if not settings.ACCOUNT_API_URL or not settings.ACCOUNT_API_TOKEN:
            logger.error("Could not process deleted accounts as account_url or account_token is not set")
            return

        try:
            headers = {
                'Authorization': 'Token ' + settings.ACCOUNT_API_TOKEN,
                'Accept': 'application/json'
            }
            last_received = config.LAST_RECEIVED_DELETED_USER
            url = settings.ACCOUNT_API_URL + '/api/users/deleted?event_time__gt=' + last_received
            r = requests.get(url, headers=headers)
        except Exception as e:
            logger.error("Error getting deleted accounts: %s", e)

        count = 0
        for orphan in r.json():
            last_received = orphan['event_time']

            try:
                user = User.objects.get(external_id=orphan['userid'])
            except ObjectDoesNotExist:
                continue

            if not user.is_active:
                continue

            user.is_active = False
            user.ban_reason = 'user deleted in account'
            user.save()
            count = count + 1

        if count:
            logger.info("Accounts blocked beacause of deleted account in pleio: %s", count)
        config.LAST_RECEIVED_DELETED_USER = last_received


@shared_task
def remove_floating_attachments(schema_name):
    with schema_context(schema_name):
        deleted = Attachment.objects.filter(attached_content_type=None).delete()
        logger.info("%s: %d floating attachments were deleted.", schema_name, len(deleted))


@shared_task
def resize_pending_images(schema_name):
    with schema_context(schema_name):
        time_threshold = timezone.now() - timedelta(hours=1)
        pending = ResizedImage.objects.filter(status=ResizedImage.PENDING, created_at__lt=time_threshold)
        for image in pending:
            celery.current_app.send_task('core.tasks.misc.image_resize', (schema_name, image.id,))
        logger.info("%s: %d pending image resizes.", schema_name, pending.count())


@shared_task
def cleanup_auditlog(schema_name):
    minimum_timestamp = timezone.now() - timedelta(days=31)
    with schema_context(schema_name):
        deletedLogs = LogEntry.objects.filter(timestamp__lt=minimum_timestamp).delete()
        logger.info("%s: %d log entries were deleted", schema_name, deletedLogs[0])


@shared_task
def depublicate_content(schema_name):
    now = timezone.now()
    with schema_context(schema_name):
        to_archive = Entity.objects.filter(schedule_archive_after__isnull=False,
                                           schedule_archive_after__lte=now,
                                           is_archived=False).select_subclasses()
        for entity in to_archive:
            entity.is_archived = True
            entity.save()

        to_delete = Entity.objects.filter(schedule_delete_after__isnull=False,
                                          schedule_delete_after__lte=now).select_subclasses()
        for entity in to_delete:
            entity.delete()
