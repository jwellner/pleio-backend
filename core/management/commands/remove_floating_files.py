import os
import logging

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

            empty_folder_count = self.remove_empty_folders(tenant)

            self.stdout.write("Removed %d floating file(s) for and %d empty folder(s) for tenant %s" % (len(floating_files), empty_folder_count, tenant.name))

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
            grounded_files = FileFolder.objects.filter(thumbnail__in=floating_files).values_list('thumbnail', flat=True)
            floating_files.difference_update(grounded_files)

            return floating_files

    def remove_file(self, tenant, file):
        base_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
        os.remove(os.path.join(base_path, file))

    def remove_empty_folders(self, tenant):
        count = 0
        base_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
        walk = list(os.walk(base_path))
        for path, _, _ in walk[::-1]:
            if path == base_path:
                continue
            if len(os.listdir(path)) == 0 and not path == base_path:
                os.rmdir(path)
                count+=1
        return count
