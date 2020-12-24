import html

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from core import config
from core.lib import tenant_schema, access_id_to_acl
from tenants.models import Client
from core.models import Entity, Group
from backend2 import settings
from elgg.helpers import ElggHelpers
from elgg.models import Instances, GuidMap, ElggObjectsEntity


class Command(BaseCommand):
    help = 'Fix html encoded strings in title and description'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_elgg_instance(self, tenant):
        all_elgg_sites = Instances.objects.using("elgg_control").all()

        if not all_elgg_sites:
            raise CommandError("""There are no elgg sites in the control database check config""")

        return Instances.objects.using("elgg_control").filter(name=tenant.elgg_database).first()

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

        self._fix_description()

        # All done!
        self.stdout.write(">> Done!\n\n")

    def _fix_description(self):
        i = 0
        entities = Entity.objects.all().select_subclasses()
        for e in entities:

            if hasattr(e, 'description'):
                if e.description == e.title:
                    in_guid_map = GuidMap.objects.filter(guid=e.guid).first()
                    if in_guid_map:
                        elgg_entity = ElggObjectsEntity.objects.using(self.import_id).filter(entity__guid=in_guid_map.id).first()
                        if elgg_entity:
                            e.description = elgg_entity.description
                            e.save()
                            i+=1

        self.stdout.write("\n>> Updated " + str(i) + " entities.")
