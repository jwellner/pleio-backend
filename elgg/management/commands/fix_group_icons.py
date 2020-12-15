import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.db import connections
from core import config
from core.lib import tenant_schema
from tenants.models import Client
from core.models import Group
from backend2 import settings
from elgg.models import (
    Instances, GuidMap
)
from elgg.helpers import ElggHelpers


class Command(BaseCommand):
    help = 'Fix group icons after migration'
    import_id = None
    helpers = None
    elgg_domain = None

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

        tenant = Client.objects.get(schema_name=schema)

        self.stdout.write("Fix group icons for tenant '%s'\n" % (tenant.schema_name))

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Migration tool did not run on this site, skipping.")
            return

        self._fix_group_icons()

        # All done!
        self.stdout.write("\n>> Done!")

    def _fix_group_icons(self):

        for group in Group.objects.all():
            if group.icon:
                # delete icon if group file does not exist 
                if not default_storage.exists(group.icon.upload.path):
                    self.stdout.write("%s does not exist, removing.\n" % group.icon.upload.path)
                    icon = group.icon
                    group.icon = None
                    group.save()
                    icon.delete()
