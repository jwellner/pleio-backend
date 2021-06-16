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
from file.models import FileFolder


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

        self._fix_folders()

        # All done!
        self.stdout.write(">> Done!\n\n")

    def _fix_folders(self):
        i = 0

        def is_loose_folder(elgg_entity):

            try:
                parent_guid = elgg_entity.entity.get_metadata_value_by_name("parent_guid")
                if parent_guid == str(0):
                    return False
                elgg_entity = ElggObjectsEntity.objects.using(self.import_id).filter(entity__guid=parent_guid).first()
                if not elgg_entity:
                    return True
                return is_loose_folder(elgg_entity)
            except Exception:
                return True
            return False


        migrated_folder_ids = FileFolder.objects.filter(parent=None).values_list('id', flat=True)
        folders = GuidMap.objects.filter(object_type='folder').filter(guid__in=migrated_folder_ids)

        for folder in folders:
            elgg_entity = ElggObjectsEntity.objects.using(self.import_id).filter(entity__guid=folder.id).first()
            if is_loose_folder(elgg_entity):
                try:
                    f = FileFolder.objects.get(id=folder.guid, is_folder=True)
                    print(f.group.name)
                    print(str(folder.id))
                    print(f.title)
                    f.delete()
                    i+=1
                except Exception:
                    self.stdout.write("\n>> Folder with guid " + str(folder.id) + " not deleted.")

        self.stdout.write("\n>> Deleted " + str(i) + " folders.")
