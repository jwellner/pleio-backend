# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from django.core import management
from tenants.models import Client, Domain

@shared_task(name='background.dispatch_cron', bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    for client in Client.objects.exclude(schema_name='public'):
        self.app.logger.info('Schedule cron {} for {}'.format(period, client.schema_name))

        domain = Domain.objects.filter(tenant_id=client.id, is_primary=True).first().domain

        url = 'https://' + domain
        if period == 'hourly':
            send_notifications.delay(url, client.schema_name)


@shared_task(name='send.notifications', bind=True)
def send_notifications(self, url, schema_name):
    # pylint: disable=unused-argument
    management.execute_from_command_line(['manage.py', 'tenant_command', 'send_notification_emails', '--url', url, '--schema', schema_name])
