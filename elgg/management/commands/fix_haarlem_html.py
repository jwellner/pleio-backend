import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from core import config
from core.lib import tenant_schema
from tenants.models import Client
from wiki.models import Wiki
from backend2 import settings
from elgg.models import (
    Instances, GuidMap
)
from elgg.helpers import ElggHelpers


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
        
        tenant = Client.objects.get(schema_name=schema)

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Import not run for tenant {tenant.schema_name}. Exiting.")
            return False


        self._fix_wiki()

        # All done!
        self.stdout.write("\n>> Done!")

    def _fix_wiki(self):

        self.stdout.write(f"Replace divs in wiki")

        wikis = Wiki.objects.all()

        count = 0

        for wiki in wikis:
            if wiki.description:
                new_description = re.sub(r'<p>(.*?)</p>', r'<div>\1</div>', wiki.description)
                if wiki.description != new_description:
                    wiki.description = new_description
                    wiki.save()
                    count+=1

        self.stdout.write(f"Updated {count} wiki's")

