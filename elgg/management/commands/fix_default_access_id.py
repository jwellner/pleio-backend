import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.db import connections
from core import config
from core.lib import tenant_schema
from tenants.models import Client
from core.models import Setting
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

        self.stdout.write("Fix DEFAULT_ACCESS_ID for tenant '%s'\n" % (tenant.schema_name))

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Migration tool did not run on this site, skipping.")
            return

        self._fix_default_access_id()

        # All done!
        self.stdout.write("\n>> Done!")

    def _fix_default_access_id(self):
        if isinstance(config.DEFAULT_ACCESS_ID, str):
            try:
                config.DEFAULT_ACCESS_ID = int(config.DEFAULT_ACCESS_ID)

                if config.DEFAULT_ACCESS_ID not in [0,1,2]:
                    config.DEFAULT_ACCESS_ID = 1

                self.stdout.write("\nDEFAULT_ACCESS_ID updated")
            except ValueError:
                self.stdout.write(f"\nInvalid value for DEFAULT_ACCESS_ID ({config.DEFAULT_ACCESS_ID}) - revert to 1")
                config.DEFAULT_ACCESS_ID = 1

