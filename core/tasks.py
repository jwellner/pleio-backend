# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.utils.log import get_task_logger

from django.core import management
from tenants.models import Client
from django_tenants.utils import schema_context
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Search
from core import config
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation
from django.utils.html import strip_tags
from django.conf import settings

from file.models import FileFolder

logger = get_task_logger(__name__)

@shared_task(bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    '''
    Dispatch period cron tasks for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Schedule cron %s for %s', period, client.schema_name)

        if period == 'hourly':
            send_notifications.delay(client.schema_name)

        if period in ['daily', 'weekly', 'monthly']:
            send_overview.delay(client.schema_name, period)

@shared_task(bind=True)
def dispatch_task(self, task, **kwargs):
    # pylint: disable=unused-argument
    '''
    Dispatch task for all tenants
    '''
    for client in Client.objects.exclude(schema_name='public'):
        logger.info('Dispatch task %s for %s', task, client.schema_name)
        self.app.tasks[task].delay(client.schema_name, *kwargs)

@shared_task(bind=True)
def send_notifications(self, schema_name):
    # pylint: disable=unused-argument
    '''
    Send notification mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_notification_emails', '--schema', schema_name])

@shared_task(bind=True)
def send_overview(self, schema_name, period):
    # pylint: disable=unused-argument
    '''
    Send overview mails for tenant
    '''
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_overview_emails', '--schema', schema_name, '--interval', period])

@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild_all(self):
    # pylint: disable=unused-argument
    # pylint: disable=protected-access
    '''
    Delete indexes and rebuild all tenants
    '''

    models = registry.get_models()

    # delete indexes
    for index in registry.get_indices(models):
        try:
            index.delete()
            logger.info('deleted index %s', index._name)
        except Exception:
            logger.info('index %s does not exist', index._name)

    for client in Client.objects.exclude(schema_name='public'):
        elasticsearch_rebuild.delay(client.schema_name)


@shared_task(bind=True, ignore_result=True)
def elasticsearch_rebuild(self, schema_name):
    # pylint: disable=unused-argument
    '''
    Rebuild search index for tenant
    '''
    with schema_context(schema_name):
        logger.info('elasticsearch_rebuild \'%s\'', schema_name)

        models = registry.get_models()

        # create indexs if not exist
        for index in registry.get_indices(models):
            try:
                index.create()
                logger.info('created index %s')
            except Exception:
                logger.info('index %s already exists')

        # delete all objects for tenant before updating
        s = Search(index='_all').query().filter(
            'term', tenant_name=schema_name
        )

        logger.info('deleting %i objects', s.count())
        s.delete()

        for doc in registry.get_documents(models):
            logger.info("indexing %i '%s' objects",
                doc().get_queryset().count(),
                doc.django.model.__name__
            )
            qs = doc().get_indexing_queryset()
            doc().update(qs, parallel=False)

@shared_task(bind=True, ignore_result=True)
def elasticsearch_index_file(self, schema_name, file_guid):
    # pylint: disable=unused-argument
    '''
    Index file for tenant
    '''
    with schema_context(schema_name):
        try:
            instance = FileFolder.objects.get(id=file_guid)
            registry.update(instance)
            registry.update_related(instance)

        except Exception as e:
            logger.error('elasticsearch_update %s %s: %s', schema_name, file_guid, e)


@shared_task(bind=True, ignore_result=True)
def send_mail_multi(self, schema_name, subject, html_template, context, email_address, reply_to=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    '''
    send email
    '''
    with schema_context(schema_name):
        if config.LANGUAGE:
            translation.activate(config.LANGUAGE)
        html_template = get_template(html_template)
        html_content = html_template.render(context)
        text_content = strip_tags(html_content)

        try:
            email = EmailMultiAlternatives(subject, text_content, settings.FROM_EMAIL, to=[email_address], reply_to=reply_to)
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            logger.error('email sent to %s failed. Error: %s', email_address, e)
