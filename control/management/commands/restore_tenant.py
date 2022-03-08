import os
import logging
from django.core.management.base import BaseCommand
from tenants.models import Client
from control.tasks import restore_site

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Restore backup to new tenant'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--backup-folder', help='Backup folder to restore', required=True)
        parser.add_argument('--schema', help='New tentant schema name', required=True)
        parser.add_argument('--domain', help='New tenant domain name', required=True)

    def handle(self, *args, **options):

        tenant = Client.objects.filter(schema_name=options['schema']).first()

        if tenant:
            self.stdout.write(f"Tenant schema already exists {options['schema']}")
            return

        task = restore_site.delay(options['backup_folder'], options['schema'], options['domain'])
        
        task.get()

        self.stdout.write(f"Succesfully resored backup to {options['schema']}")

