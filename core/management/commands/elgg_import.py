from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core import config
from backend2 import settings
from core.elgg_models import Instances, ElggUsersEntity
from user.models import User
from datetime import datetime, timedelta
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError

class Command(InteractiveTenantOption, BaseCommand):
    help = 'Import elgg site'

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

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)
        
        self.stdout.write("Start import elgg database %s to tenant %s\n" % (elgg_instance.name, tenant.schema_name))

        import_id = "import_%s" % elgg_instance.name

        # change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"]
        elgg_database_settings["id"] = import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[import_id] = elgg_database_settings

        # change default connection to tenant
        connection.set_tenant(tenant)

        users = ElggUsersEntity.objects.using(import_id)

        self.stdout.write("# Users\n")
        self.stdout.write("Total: %i\n" % users.count())
        for u in users:
            # Validate data
            # TODO: how and what should we validate?

            # Create new User
            user = User(
                email=u.email,
                name=u.name,
                external_id=u.pleio_guid
            )

            try:
                # user.save()
                self.stdout.write("- imported %s with guid %i to %s\n" % (u.email, u.guid, user.id))
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

            # TODO: store old guid -> new guid conversion?
            
