# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.utils.log import get_task_logger

from django.core import management
from tenants.models import Client
from django_tenants.utils import schema_context
from django_elasticsearch_dsl.registries import registry

from file.models import FileFolder

logger = get_task_logger(__name__)

@shared_task(name='background.dispatch_cron', bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Schedule cron %s for %s', period, client.schema_name)

        if period == 'hourly':
            send_notifications.delay(client.schema_name)
        
        if period in ['daily', 'weekly', 'monthly']:
            send_overview.delay(client.schema_name, period)


@shared_task(name='send.notifications', bind=True)
def send_notifications(self, schema_name):
    # pylint: disable=unused-argument
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_notification_emails', '--schema', schema_name])

@shared_task(name='send.overview', bind=True)
def send_overview(self, schema_name, period):
    # pylint: disable=unused-argument
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_overview_emails', '--schema', schema_name, '--interval', period])

@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild(self, schema_name):
    # pylint: disable=unused-argument
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild \'%s\'', schema_name)

        models = registry.get_models()

        for doc in registry.get_documents(models):
            logger.info("Indexing %i '%s' objects",
                doc().get_queryset().count(),
                doc.django.model.__name__
            )
            qs = doc().get_indexing_queryset()
            doc().update(qs, parallel=False)

@shared_task(bind=True, ignore_result=True)
def elasticsearch_index_file(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    with schema_context(schema_name):
        try:
            instance = FileFolder.objects.get(id=file_guid)
            registry.update(instance)
            registry.update_related(instance)

        except Exception as e:
            logger.error('elasticsearch_update %s %s: %s', schema_name, file_guid, e)
