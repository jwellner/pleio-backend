from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core import config
from core.lib import ACCESS_TYPE, access_id_to_acl
from core.models import ProfileField, UserProfile, UserProfileField, Group
from backend2 import settings
from elgg.models import Instances, ElggUsersEntity, GuidMap, ElggSitesEntity, ElggGroupsEntity
from elgg.helpers import ElggHelpers
from elgg.mapper import Mapper
from user.models import User
from datetime import datetime
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError

import json
import html

class Command(InteractiveTenantOption, BaseCommand):
    help = 'Import elgg site'
    import_id = None
    helpers = None
    mapper = None
    dry = False

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
        parser.add_argument('--dry-run', help='do not save data', default=False, action="store_true")
        parser.add_argument('--flush', help='clean tenant database before import', default=False, action="store_true")

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        self.dry = options.get("dry-run")
        
        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Import elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        if options.get("flush"):
            # docker-compose exec admin python manage.py tenant_command flush --schema test2 --no-input
            self.stdout.write(f"* flush database {tenant.schema_name}")
            management.execute_from_command_line(['manage.py', 'tenant_command', 'flush', '--schema', tenant.schema_name, '--no-input'])

        if self.dry:
            self.stdout.write("- running in dry-run mode, not saving data")

        self.import_id = "import_%s" % elgg_instance.name

        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"]
        elgg_database_settings["id"] = self.import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[self.import_id] = elgg_database_settings

        # Change default connection to tenant
        connection.set_tenant(tenant)

        self.helpers = ElggHelpers(self.import_id)
        self.mapper = Mapper(self.import_id)

        # Clean GuidMap (maybe we can use it to check if import is already done?)

        if self.dry:
            GuidMap.objects.all().delete()

        if GuidMap.objects.count() > 0:
            self.stdout.write(f"Import already run on tenant {tenant.schema_name}. Exiting.")
            return False

        self._import_settings()
        self._import_users()
        self._import_groups()

        # All done!
        self.stdout.write("\n>> Done!")

        if self.dry:
            GuidMap.objects.all().delete()

    def _import_settings(self):

        self.stdout.write("\n>> Settings (x) ", ending="")

        elgg_site = ElggSitesEntity.objects.using(self.import_id).first()

        config.NAME = html.unescape(elgg_site.name)
        config.SUBTITLE = html.unescape(elgg_site.description)
        config.THEME = self.helpers.get_plugin_setting("theme")
        config.ACHIEVEMENTS_ENABLED = self.helpers.get_plugin_setting("achievements_enabled") == "yes"
        config.CANCEL_MEMBERSHIP_ENABLED = self.helpers.get_plugin_setting("cancel_membership_enabled") == "yes"
        config.DEFAULT_ACCESS_ID = self.helpers.get_site_config('default_access')
        config.LANGUAGE = self.helpers.get_site_config('language') if self.helpers.get_site_config('language') else "nl"
        # config.LOGO = TODO: check /mod/pleio_template/logo.php
        config.LOGO_ALT = html.unescape(self.helpers.get_plugin_setting("logo_alt"))
        # config.ICON = TODO: check /mod/pleio_template/icon.php
        config.ICON_ALT = html.unescape(self.helpers.get_plugin_setting("icon_alt"))
        config.ICON_ENABLED = self.helpers.get_plugin_setting("show_icon") == "yes"
        config.STARTPAGE = self.helpers.get_plugin_setting("startpage") # TODO: what if CMS page, convert to guid?
        config.LEADER_ENABLED = self.helpers.get_plugin_setting("show_leader") == "yes"
        config.LEADER_BUTTONS_ENABLED = self.helpers.get_plugin_setting("show_leader_buttons") == "yes"
        config.LEADER_IMAGE = self.helpers.get_plugin_setting("leader_image") # TODO: convert URL ?
        config.INITIATIVE_ENABLED = self.helpers.get_plugin_setting("show_initiative") == "yes"
        config.INITIATIVE_TITLE = html.unescape(self.helpers.get_plugin_setting("initiative_title"))
        config.INITIATIVE_IMAGE = self.helpers.get_plugin_setting("initiative_image")
        config.INITIATIVE_IMAGE_ALT = html.unescape(self.helpers.get_plugin_setting("initiative_image_alt"))
        config.INITIATIVE_DESCRIPTION = html.unescape(self.helpers.get_plugin_setting("initiative_description"))
        config.INITIATOR_LINK = self.helpers.get_plugin_setting("initiator_link")
        config.STYLE = {
            'font': self.helpers.get_plugin_setting("font"),
            'colorPrimary': self.helpers.get_plugin_setting("color_primary"),
            'colorSecondary': self.helpers.get_plugin_setting("color_secondary"),
            'colorHeader': self.helpers.get_plugin_setting("color_header")
        }
        config.CUSTOM_TAGS_ENABLED = self.helpers.get_plugin_setting("custom_tags_allowed")
        config.TAG_CATEGORIES = json.loads(html.unescape(self.helpers.get_plugin_setting("tagCategories")))
        config.ACTIVITY_FEED_FILTERS_ENABLED = self.helpers.get_plugin_setting("show_extra_homepage_filters") == "yes"
        config.MENU = json.loads(html.unescape(self.helpers.get_plugin_setting("menu")))
        config.FOOTER = json.loads(html.unescape(self.helpers.get_plugin_setting("footer")))
        config.DIRECT_LINKS = json.loads(html.unescape(self.helpers.get_plugin_setting("directLinks")))
        config.SHOW_LOGIN_REGISTER = self.helpers.get_plugin_setting("show_extra_homepage_filters")

        self.stdout.write(".", ending="")

    def _import_groups(self):
        # Groups
        elgg_groups = ElggGroupsEntity.objects.using(self.import_id)

        subgroups_enabled = True if self.helpers.get_plugin_setting("profile") == "yes" else False

        self.stdout.write("\n>> Groups (%i) " % elgg_groups.count(), ending="")

        for elgg_group in elgg_groups:

            group = self.mapper.get_group(elgg_group)

            if not self.dry:
                owner = User.objects.get(id=GuidMap.objects.get(id=elgg_group.entity.owner_guid).guid)
                group.owner = owner
                group.save()

                # first add members
                relations = elgg_group.entity.relation_inverse.filter(relationship="member", left__type='user')
                for relation in relations:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)
                    group.join(user, "member")

                    # also check of user is subscribed
                    subscribed = elgg_group.entity.relation_inverse.filter(relationship="subscribed", left__type='user', left__guid=relation.left.guid).first()
                    if subscribed:
                        user.profile.group_notifications.append(group.id)
                        user.profile.save()

                # then update or add admins
                relations = elgg_group.entity.relation_inverse.filter(relationship="group_admin", left__type='user')
                for relation in relations:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)
                    group.join(user, "admin")

                # finally update or add owner
                group.join(owner, 'owner')

                # TODO: subgroups
                if subgroups_enabled:
                    pass

            self.stdout.write(".", ending="")

    def _import_users(self):
        # Load site entity
        site = ElggSitesEntity.objects.using(self.import_id).first()

        # Import site profile settings
        profile = self.helpers.get_plugin_setting("profile")

        # Store fields for later use
        profile_fields = []

        if profile:
            profile_items = json.loads(profile)
            self.stdout.write("\n>> ProfileItems (%i) " % len(profile_items), ending="")
            for item in profile_items:

                profile_field = self.mapper.get_profile_field(item)
                profile_fields.append(profile_field)

                if not self.dry:
                    profile_field.save()
                self.stdout.write(".", ending="")

        # Import users
        elgg_users = ElggUsersEntity.objects.using(self.import_id)

        self.stdout.write("\n>> Users (%i) " % elgg_users.count(), ending="")

        for elgg_user in elgg_users:
            user = self.mapper.get_user(elgg_user)

            try:
                if not self.dry:
                    user.save()

                user_profile = self.mapper.get_user_profile(elgg_user)
                user_profile.user = user

                if not self.dry:
                    user_profile.save()

                # get user profile field data
                for field in profile_fields:
                    user_profile_field = self.mapper.get_user_profile_field(elgg_user, user_profile, field, user)
                    if not self.dry and user_profile_field:
                        user_profile_field.save()

                GuidMap.objects.create(id=elgg_user.entity.guid, guid=user.guid, object_type='user')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def debug_model(self, model):
        self.stdout.write(', '.join("%s: %s" % item for item in vars(model).items() if not item[0].startswith('_')))
