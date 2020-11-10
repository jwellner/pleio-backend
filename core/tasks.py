# Create your tasks here
from __future__ import absolute_import, unicode_literals

import csv
import os

from celery import shared_task
from celery.utils.log import get_task_logger

from django.core import management
from tenants.models import Client
from django_tenants.utils import schema_context
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Search
from core import config
from core.lib import html_to_text, access_id_to_acl
from core.models import ProfileField, UserProfileField
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation
from django.conf import settings
from user.models import User
from django.utils.translation import ugettext_lazy

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
        text_content = html_to_text(html_content)
        from_mail = f"{config.NAME} <{settings.FROM_EMAIL}>"

        try:
            email = EmailMultiAlternatives(subject, text_content, from_mail, to=[email_address], reply_to=reply_to)
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            logger.error('email sent to %s failed. Error: %s', email_address, e)


def get_import_users_data(fields, row):
    data = {}
    for field in fields:
        field['value'] = row[field['csvColumn']]
        data[field['userField']] = field
    return data


def get_import_users_user(data):

    if 'id' in data:
        try:
            return User.objects.get(id=data['id']['value'])
        except Exception:
            pass
    if 'email' in data:
        try:
            return User.objects.get(email=data['email']['value'])
        except Exception:
            pass

    return False

@shared_task(bind=True, ignore_result=True)
def import_users(self, schema_name, fields, csv_location, performing_user_guid):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Import users
    '''
    with schema_context(schema_name):

        performing_user = User.objects.get(id=performing_user_guid)

        stats = {
            'created': 0,
            'updated': 0,
            'error': 0
        }

        logger.info("Start import on tenant %s by user", performing_user.email)

        success = False
        error_message = ''

        try:
            with open(csv_location) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    data = get_import_users_data(fields, row)
                    user = get_import_users_user(data)

                    if not user:
                        if 'name' in data and 'email' in data:
                            try:
                                user = User.objects.create(email=data['email']['value'], name=data['name']['value'])
                                stats['created'] += 1
                            except Exception:
                                stats['error'] += 1
                        else:
                            stats['error'] += 1
                    else:
                        stats['updated'] += 1

                    if user:
                        # create profile fields
                        for field, values in {d: data[d] for d in data if d not in ['id', 'email', 'name']}.items():

                            profile_field = ProfileField.objects.get(id=field)

                            if profile_field:
                                user_profile_field, created = UserProfileField.objects.get_or_create(
                                    profile_field=profile_field,
                                    user_profile=user.profile
                                )

                                user_profile_field.value = values['value']

                                if created:
                                    user_profile_field.read_access = access_id_to_acl(user, values['accessId'])
                                elif values['forceAccess']:
                                    user_profile_field.read_access = access_id_to_acl(user, values['accessId'])

                                user_profile_field.save()

            success = True

            os.remove(csv_location)

            logger.info("Import done with stats: %s ", stats)
        except Exception as e:
            error_message = "Import failed with message %s" % e
            logger.error(error_message)

        subject = ugettext_lazy("Import was a success") if success else ugettext_lazy("Import failed")
        template = "email/user_import_success.html" if success else "email/user_import_failed.html"

        tenant = Client.objects.get(schema_name=schema_name)
        context = {
            'site_name': config.NAME,
            'site_url': 'https://' + tenant.domains.first().domain,
            'primary_color': config.COLOR_PRIMARY,
            'user_name': performing_user.name,
            'stats_created': stats.get('created', 0),
            'stats_updated': stats.get('updated', 0),
            'stats_error': stats.get('error', 0),
            'error_message': error_message
        }

        send_mail_multi.delay(schema_name, subject, template, context, performing_user.email)
