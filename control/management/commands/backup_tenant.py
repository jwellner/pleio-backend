import os
import logging
from django.core.management.base import BaseCommand
from tenants.models import Client
from control.tasks import backup_site

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backup tenant to folder'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--schema', help='Tenant schema name', required=True)
        parser.add_argument('--backup-folder', help='The backup folder name')
        parser.add_argument('--skip-files', help='Skip files backup', default=False, action="store_true")
        parser.add_argument('--compress', help='Create a zipfile', default=False, action="store_true")

    def handle(self, *args, **options):
        tenant = Client.objects.filter(schema_name=options['schema']).first()

        if not tenant:
            self.stdout.write(f"Could not find tenant {options['schema']}")
            return

        task = backup_site.delay(tenant.id,
                                 skip_files=options['skip_files'],
                                 backup_folder=options['backup_folder'],
                                 compress=options['compress'])

        result = task.get()

        self.stdout.write(result)
