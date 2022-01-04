import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context, tenant_context
from core.models.attachment import Attachment
from file.models import FileFolder
from tenants.models import Client

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup for all files without a related database entry'

    def handle(self, *args, **options):
        with schema_context('public'):
            tenants = Client.objects.exclude(schema_name='public')

        files_removed = 0

        for tenant in tenants:
            floating_files = self.get_floating_files(tenant)
            for file in floating_files:
                self.remove_file(tenant, file)
                files_removed += 1

            if floating_files:
                logger.warning("Removed %d floating files for %s", len(floating_files), tenant.name)
            else:
                logger.warning("No files to remove for %s", tenant.name)

    def get_floating_files(self, tenant):
        base_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
        with tenant_context(tenant):
            floating_files = set()
            for root, __, files in os.walk(base_path):
                relative_root = root.removeprefix(base_path).removeprefix('/')
                for file in files:
                    floating_files.add(os.path.join(relative_root, file))

            grounded_files = Attachment.objects.filter(upload__in=floating_files).values_list('upload', flat=True)
            floating_files.difference_update(grounded_files)
            grounded_files = FileFolder.objects.filter(upload__in=floating_files).values_list('upload', flat=True)
            floating_files.difference_update(grounded_files)

            return floating_files

    def remove_file(self, tenant, file):
        base_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
        os.remove(os.path.join(base_path, file))
