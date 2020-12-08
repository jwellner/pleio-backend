import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from core import config
from core.models import Group, Entity, Comment, Widget
from backend2 import settings
from elgg.models import (
    Instances, GuidMap, ElggSitesEntity
)
from elgg.helpers import ElggHelpers
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError
from core.tasks import replace_domain_links
from core.lib import tenant_schema


class Command(InteractiveTenantOption, BaseCommand):
    help = 'Replace links after import'
    import_id = None
    helpers = None
    elgg_domain = None
    tenant_domain = None

    def get_elgg_from_options_or_interactive(self, **options):
        all_elgg_sites = Instances.objects.using("elgg_control").all()

        if not all_elgg_sites:
            raise CommandError("""There are no elgg sites in the control database check config""")

        if options.get('elgg'):
            elgg_database = options['elgg']
        else:
            while True:
                elgg_database = input("Enter elgg database ('?' to list databases): ")
                if elgg_database == '?':
                    print('\n'.join(["%s" % s.name for s in all_elgg_sites]))
                else:
                    break

        if elgg_database not in [s.name for s in all_elgg_sites]:
            raise CommandError("Invalid database, '%s'" % (elgg_database,))

        return Instances.objects.using("elgg_control").get(name=elgg_database)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--elgg', help='elgg database')
        parser.add_argument('--elgg_domain', help='elgg domain')

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        self.elgg_domain = options.get("elgg_domain", None)

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Import elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        self.import_id = "import_%s" % elgg_instance.name

        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"]
        elgg_database_settings["id"] = self.import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[self.import_id] = elgg_database_settings

        # Change default connection to tenant
        connection.set_tenant(tenant)

        self.helpers = ElggHelpers(self.import_id)

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Import not run for tenant {tenant.schema_name}. Exiting.")
            return False

        elgg_site = ElggSitesEntity.objects.using(self.import_id).first()

        if not self.elgg_domain:
            matches = re.findall(r'http(?:s)?\:\/\/(.+)\/', elgg_site.url)
            self.elgg_domain = matches[0]

        self.tenant_domain = tenant.get_primary_domain().domain

        if not self.elgg_domain:
            self.stdout.write(f"Unable to get elgg domain. Exiting.")
            return False

        if not self.tenant_domain:
            self.stdout.write(f"Unable to get primary tenant domain. Exiting.")
            return False

        self.stdout.write(f"Found elgg domain {self.elgg_domain} and tenant domain {self.tenant_domain}")

        replace_domain_links.delay(tenant_schema(), self.elgg_domain, True)
   