import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from core import config
from core.models import Group, Entity, Comment, Widget
from backend2 import settings
from elgg.models import (
    Instances, GuidMap, ElggSitesEntity, ElggObjectsEntity
)
from elgg.helpers import ElggHelpers
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError


class Command(InteractiveTenantOption, BaseCommand):
    help = 'Fix access rights after migration'
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

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Fix access elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

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

        self._fix_access()

        # All done!
        self.stdout.write("\n>> Done!")

    def _fix_access(self):

        entities = Entity.objects.exclude(group=None).select_subclasses()

        for entity in entities:
            # check if entity was imported
            in_guid_map = GuidMap.objects.filter(guid=entity.guid).first()
            if in_guid_map:
                self.stdout.write(f"{entity.type_to_string}:{entity.title}")

                elgg_entity = ElggObjectsEntity.objects.using(self.import_id).filter(entity__guid=in_guid_map.id).first()
                
                if elgg_entity:

                    if entity.type_to_string in ['file', 'folder', 'wiki']:
                        write_access_id = int(elgg_entity.entity.get_metadata_value_by_name("write_access_id")) \
                            if elgg_entity.entity.get_metadata_value_by_name("write_access_id") else 0

                        entity.write_access = self.helpers.elgg_access_id_to_acl(entity, write_access_id)
                        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)
                        entity.save()
                        self.stdout.write(f"> update write_access {entity.write_access} ({write_access_id})")
                        self.stdout.write(f"> update read_access {entity.read_access} ({elgg_entity.entity.access_id})")
                    else:

                        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)
                        entity.save()
                        self.stdout.write(f"> update read_access {entity.read_access} ({elgg_entity.entity.access_id})")

                else:
                    self.stdout.write(f"ERROR, NOT FOUND IN ELGG DB")

            else:
                self.stdout.write('X')
