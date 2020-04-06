from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core import config
from core.lib import ACCESS_TYPE, access_id_to_acl
from core.models import ProfileField, UserProfile, UserProfileField, Group, Entity, Comment
from backend2 import settings
from elgg.models import Instances, ElggUsersEntity, GuidMap, ElggSitesEntity, ElggGroupsEntity, ElggObjectsEntity
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
        parser.add_argument('--flush', help='clean tenant database before import', default=False, action="store_true")

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return


        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Import elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        if options.get("flush"):
            # docker-compose exec admin python manage.py tenant_command flush --schema test2 --no-input
            self.stdout.write(f"* flush database {tenant.schema_name}")
            management.execute_from_command_line(['manage.py', 'tenant_command', 'flush', '--schema', tenant.schema_name, '--no-input'])

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

        if GuidMap.objects.count() > 0:
            self.stdout.write(f"Import already run on tenant {tenant.schema_name}. Exiting.")
            return False

        self._import_settings()
        self._import_users()
        self._import_groups()
        self._import_blogs()
        self._import_news()
        self._import_events()
        self._import_discussions()

        # All done!
        self.stdout.write("\n>> Done!")

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

        config.FONT = self.helpers.get_plugin_setting("font")
        config.COLOR_PRIMARY = self.helpers.get_plugin_setting("color_primary")
        config.COLOR_SECONDARY = self.helpers.get_plugin_setting("color_secondary")
        config.COLOR_HEADER = self.helpers.get_plugin_setting("color_header")
        config.CUSTOM_TAGS_ENABLED = self.helpers.get_plugin_setting("custom_tags_allowed") == "yes"
        config.TAG_CATEGORIES = json.loads(html.unescape(self.helpers.get_plugin_setting("tagCategories")))
        config.ACTIVITY_FEED_FILTERS_ENABLED = self.helpers.get_plugin_setting("show_extra_homepage_filters") == "yes"
        config.MENU = json.loads(html.unescape(self.helpers.get_plugin_setting("menu")))
        config.FOOTER = json.loads(html.unescape(self.helpers.get_plugin_setting("footer")))
        config.DIRECT_LINKS = json.loads(html.unescape(self.helpers.get_plugin_setting("directLinks")))
        config.SHOW_LOGIN_REGISTER = self.helpers.get_plugin_setting("show_login_register") == "yes"
        config.ADVANCED_PERMISSIONS_ENABLED = self.helpers.get_plugin_setting("advanced_permissions") == "yes"

        self.stdout.write(".", ending="")

    def _import_groups(self):
        # Groups
        elgg_groups = ElggGroupsEntity.objects.using(self.import_id)

        subgroups_enabled = True if self.helpers.get_plugin_setting("profile") == "yes" else False

        self.stdout.write("\n>> Groups (%i) " % elgg_groups.count(), ending="")

        for elgg_group in elgg_groups:

            group = self.mapper.get_group(elgg_group)
            group.save()

            # first add members
            relations = elgg_group.entity.relation_inverse.filter(relationship="member", left__type='user')
            for relation in relations:
                user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)

                # check if user has notifications enabled
                enabled_notifications = True if elgg_group.entity.relation_inverse.filter(
                        relationship="subscribed",
                        left__type='user',
                        left__guid=relation.left.guid
                    ).first() else False

                group.members.update_or_create(
                    user=user,
                    defaults={
                        'type': 'member',
                        'enable_notification': enabled_notifications
                    }
                )

            # then update or add admins
            relations = elgg_group.entity.relation_inverse.filter(relationship="group_admin", left__type='user')
            for relation in relations:
                user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)

                # check if user has notifications enabled
                enabled_notifications = True if elgg_group.entity.relation_inverse.filter(
                        relationship="subscribed",
                        left__type='user',
                        left__guid=relation.left.guid
                    ).first() else  False

                group.members.update_or_create(
                    user=user,
                    defaults={
                        'type': 'admin',
                        'enable_notification': enabled_notifications
                    }
                )

            # finally update or add owner
            enabled_notifications = True if elgg_group.entity.relation_inverse.filter(
                    relationship="subscribed",
                    left__type='user',
                    left__guid=elgg_group.entity.owner_guid
                ).first() else False

            group.members.update_or_create(
                user=group.owner,
                defaults={
                    'type': 'owner',
                    'enable_notification': enabled_notifications
                }
            )

            # TODO: subgroups
            if subgroups_enabled:
                pass

            GuidMap.objects.create(id=elgg_group.entity.guid, guid=group.guid, object_type='group')

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
                profile_field.save()
                profile_fields.append(profile_field)

                self.stdout.write(".", ending="")

        # Import users
        elgg_users = ElggUsersEntity.objects.using(self.import_id)

        self.stdout.write("\n>> Users (%i) " % elgg_users.count(), ending="")

        for elgg_user in elgg_users:
            user = self.mapper.get_user(elgg_user)

            try:
                user.save()

                user_profile = self.mapper.get_user_profile(elgg_user)
                user_profile.user = user
                user_profile.save()

                # get user profile field data
                for field in profile_fields:
                    user_profile_field = self.mapper.get_user_profile_field(elgg_user, user_profile, field, user)
                    if user_profile_field:
                        user_profile_field.save()

                GuidMap.objects.create(id=elgg_user.entity.guid, guid=user.guid, object_type='user')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_blogs(self):
        elgg_blogs = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='blog')

        self.stdout.write("\n>> Blogs (%i) " % elgg_blogs.count(), ending="")

        for elgg_blog in elgg_blogs:
            blog = self.mapper.get_blog(elgg_blog)

            try:
                blog.save()

                self._import_comments_for(blog, elgg_blog.entity.guid)

                GuidMap.objects.create(id=elgg_blog.entity.guid, guid=blog.guid, object_type='blog')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_news(self):
        elgg_news_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='news')

        self.stdout.write("\n>> News (%i) " % elgg_news_items.count(), ending="")

        for elgg_news in elgg_news_items:
            news = self.mapper.get_news(elgg_news)

            try:
                news.save()

                self._import_comments_for(news, elgg_news.entity.guid)

                GuidMap.objects.create(id=elgg_news.entity.guid, guid=news.guid, object_type='news')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_events(self):
        elgg_event_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='event')

        self.stdout.write("\n>> Events (%i) " % elgg_event_items.count(), ending="")

        for elgg_event in elgg_event_items:
            event = self.mapper.get_event(elgg_event)

            try:
                event.save()

                # attending
                relations = elgg_event.entity.relation.filter(relationship="event_attending", right__type='user')
                for relation in relations:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)

                    event.attendees.update_or_create(
                        user=user,
                        state="accept",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                # maybe
                relations = elgg_event.entity.relation.filter(relationship="event_maybe", right__type='user')
                for relation in relations:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)

                    event.attendees.update_or_create(
                        user=user,
                        state="maybe",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                # reject
                relations = elgg_event.entity.relation.filter(relationship="event_reject", right__type='user')
                for relation in relations:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)

                    event.attendees.update_or_create(
                        user=user,
                        state="reject",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                # attending without account
                relations = elgg_event.entity.relation.filter(relationship="event_attending", right__type='object')
                for relation in relations:

                    event.attendees.update_or_create(
                        email=relation.right.get_metadata_value_by_name("email"),
                        name=relation.right.get_metadata_value_by_name("name"),
                        user=None,
                        state="accept",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                #TODO: attending without account that still have to be confirmed? skipped for now.

                self._import_comments_for(event, elgg_event.entity.guid)

                GuidMap.objects.create(id=elgg_event.entity.guid, guid=event.guid, object_type='event')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_discussions(self):
        elgg_discussion_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='discussion')

        self.stdout.write("\n>> Discussions (%i) " % elgg_discussion_items.count(), ending="")

        for elgg_discussion in elgg_discussion_items:
            discussion = self.mapper.get_discussion(elgg_discussion)

            try:
                discussion.save()

                self._import_comments_for(discussion, elgg_discussion.entity.guid)

                GuidMap.objects.create(id=elgg_discussion.entity.guid, guid=discussion.guid, object_type='discussion')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass


    def _import_comments_for(self, entity: Entity, elgg_guid):
        elgg_comment_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='comment', entity__container_guid=elgg_guid)

        for elgg_comment in elgg_comment_items:
            comment = self.mapper.get_comment(elgg_comment)

            try:
                comment.container = entity
                comment.save()

                GuidMap.objects.create(id=elgg_comment.entity.guid, guid=comment.guid, object_type='comment')
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def debug_model(self, model):
        self.stdout.write(', '.join("%s: %s" % item for item in vars(model).items() if not item[0].startswith('_')))
