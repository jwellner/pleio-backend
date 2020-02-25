from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core import config
from core.lib import ACCESS_TYPE, access_id_to_acl
from core.models import ProfileField, UserProfile, UserProfileField
from backend2 import settings
from elgg.models import Instances, ElggUsersEntity, GuidMap, ElggSitesEntity
from elgg.helpers import ElggHelpers
from user.models import User
from datetime import datetime, timedelta
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError

import json


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
        parser.add_argument('--dry', help='elgg database', default=False, action="store_true")

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        dry = options.get("dry")

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Start import elgg database %s to tenant %s\n" % (elgg_instance.name, tenant.schema_name))
        if dry:
            self.stdout.write("!!! dry run !!!")

        import_id = "import_%s" % elgg_instance.name

        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"]
        elgg_database_settings["id"] = import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[import_id] = elgg_database_settings

        # Change default connection to tenant
        connection.set_tenant(tenant)

        helpers = ElggHelpers(import_id)

        # Clean GuidMap (maybe we can use it to check if import is already done?)
        if GuidMap.objects.count() > 0:
            self.stdout.write(f"Import already run on tenant {tenant.schema_name}. Exiting.")
            return False

        # Load site entity
        site = ElggSitesEntity.objects.using(import_id).first()

        # Import site profile settings
        profile = helpers.get_plugin_setting("profile")
        profile_fields = []

        if profile:
            profile_items = json.loads(profile)
            self.stdout.write("\n>> ProfileItems (%i) " % len(profile_items), ending="")
            for item in profile_items:

                profile_field = ProfileField()
                profile_field.key = item.get("key")
                profile_field.name = item.get("name")
                profile_field.category = helpers.get_profile_category(item.get("key"))
                profile_field.field_type = helpers.get_profile_field_type(item.get("key"))
                profile_field.field_options = helpers.get_profile_options(item.get("key"))
                profile_field.is_editable_by_user = helpers.get_profile_is_editable(item.get("key"))
                profile_field.is_filter = True if item.get("name") is True else False

                profile_fields.append(profile_field)
                if not dry:
                    profile_field.save()
                self.stdout.write(".", ending="")

        # Import users
        users = ElggUsersEntity.objects.using(import_id)

        self.stdout.write("\n>> Users (%i) " % users.count(), ending="")

        for u in users:
            # Validate data ?

            # Create new User
            user = User()
            user.email = u.email if u.email != '' else f'deleted@{user.guid}'
            user.name = u.name
            user.external_id = u.pleio_guid
            user.created_at = datetime.fromtimestamp(u.entity.time_created)
            user.is_active = True if u.banned == 'no' else False

            try:
                if not dry:
                    user.save()

                # Prepare User profile data
                last_online = datetime.fromtimestamp(u.last_action) if u.last_action > 0 else None
                interval_private = u.entity.private.filter(name__startswith="email_overview_").first()
                receive_notification_metadata = u.entity.metadata.filter(name__string="notification:method:email").first()
                if receive_notification_metadata:
                    receive_notification_email = True if receive_notification_metadata.value.string == "1" else False
                else:
                    receive_notification_email = False

                receive_newsletter = True if u.entity.relation.filter(relationship="subscribed", right__guid=site.guid).first() else False

                # Create User profile
                up = UserProfile()
                up.user = user
                up.last_online = last_online
                up.group_notifications = [] # TODO: should be added when adding groups
                up.overview_email_interval = interval_private.value if interval_private else 'weekly' # TODO: should get default for site
                up.overview_email_tags = [] # Not implemented uet
                up.receive_newsletter = receive_newsletter
                up.receive_notification_email = receive_notification_email

                if not dry:
                    up.save()

                # Import User profile data
                for field in profile_fields:
                    metadata = u.entity.metadata.filter(name__string=field.key).first()
                    if metadata:
                        upf = UserProfileField()
                        upf.profile_field = field
                        upf.user_profile = up
                        upf.value = metadata.value.string
                        upf.write_access = [ACCESS_TYPE.user.format(user.guid)]
                        upf.read_access = access_id_to_acl(user, metadata.access_id)

                        if not dry:
                            upf.save()

                GuidMap.objects.create(id=u.entity.guid, guid=user.guid, object_type='user')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass


        # All done!
        self.stdout.write("\n>> Done!")

        if dry:
            GuidMap.objects.all().delete()
