import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from core import config
from core.lib import tenant_schema, access_id_to_acl
from tenants.models import Client
from file.models import FileFolder
from backend2 import settings


class Command(BaseCommand):
    help = 'Fix wiki access rights after migration'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        # check if command is run with tenant
        schema = tenant_schema()

        if schema == 'public':
            self.stdout.write("Don't run on public schema\n")
            return

        self._fix_access()

        # All done!
        self.stdout.write(">> Done!\n\n")

    def _fix_access(self):

        files = FileFolder.objects.filter(parent=None, group=None, is_folder=False)
        access_id = config.DEFAULT_ACCESS_ID
        self.stdout.write("\n>> Alter " + str(len(files)) + " files in content.")
        for f in files:
           f.read_access = access_id_to_acl(f, access_id)
           f.save()
