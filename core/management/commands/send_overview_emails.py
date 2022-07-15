from django.core.management.base import BaseCommand
from django.db import connection

from core.tasks import send_overview


class Command(BaseCommand):
    help = 'Send overview emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', dest='interval', required=True, choices=['daily', 'weekly', 'monthly'],
            help='interval of overview emails(daily, weekly, or monthly)',
        )

    def handle(self, *args, **options):
        if connection.schema_name == 'public':
            return

        send_overview.delay(connection.schema_name, options['interval'])
