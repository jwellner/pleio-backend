# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task

from django.core import management
from tenants.models import Client

@shared_task(name='background.dispatch_cron', bind=True)
def dispatch_crons(self, period):
    # pylint: disable=unused-argument
    for client in Client.objects.exclude(schema_name='public'):
        self.app.logger.info('Schedule cron {} for {}'.format(period, client.schema_name))

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
