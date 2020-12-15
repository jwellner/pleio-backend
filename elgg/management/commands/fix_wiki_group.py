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
    import_id = None
    helpers = None
    elgg_domain = None
    tenant_domain = None

    def get_elgg_instance(self, tenant):
        all_elgg_sites = Instances.objects.using("elgg_control").all()

        if not all_elgg_sites:
            raise CommandError("""There are no elgg sites in the control database check config""")

        return Instances.objects.using("elgg_control").filter(name=tenant.elgg_database).first()

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

        elgg_instance = self.get_elgg_instance(tenant)
        if not elgg_instance:
            self.stdout.write("No elgg database for schema %s\n" % schema)
            return

        self.stdout.write("Fix wiki group ACL, elgg database '%s' tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        self.import_id = "import_%s" % elgg_instance.name

        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"].copy()
        elgg_database_settings["id"] = self.import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[self.import_id] = elgg_database_settings

        self.helpers = ElggHelpers(self.import_id)

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Import not run for tenant {tenant.schema_name}. Exiting.")
            return False

        self._fix_access()

        # All done!
        self.stdout.write("\n>> Done!")

    def _fix_access(self):

        wikis = Wiki.objects.filter(parent=None).exclude(group=None)

        for wiki in wikis:
           self.helpers.update_wiki_children_acl(wiki)

