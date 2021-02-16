from auditlog.registry import auditlog
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core import config
from core.lib import is_valid_domain
from core.models import (
    ProfileField, UserProfile, UserProfileField, Group, Entity, Comment, Widget, SiteAccessRequest,
    SiteInvitation, GroupInvitation
)
from backend2 import settings
from elgg.models import (
    Instances, ElggUsersEntity, GuidMap, ElggSitesEntity, ElggGroupsEntity, ElggObjectsEntity, ElggNotifications,
    ElggAnnotations, ElggMetastrings, ElggAccessCollections, ElggEntities, PleioRequestAccess
)
from phpserialize import unserialize
from elgg.helpers import ElggHelpers
from elgg.mapper import Mapper
from user.models import User
from file.models import FileFolder
from wiki.models import Wiki
from datetime import datetime
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection, close_old_connections
from django.db import IntegrityError
from django.db.models import ObjectDoesNotExist

import json
import html
import pydash


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
        elgg_database_settings = settings.DATABASES["elgg_control"].copy()
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

        # disable auditlog
        for model in auditlog.get_models():
            auditlog.unregister(model)

        tenant.elgg_database = elgg_instance.name
        tenant.save()

        self._import_users()
        self._import_settings()
        self._import_groups()

        self._import_file_folders()
        self._import_files()

        self._import_wikis()
        self._import_blogs()
        self._import_news()
        self._import_events()
        self._import_discussions()
        self._import_questions()
        self._import_tasks()
        self._import_pages()
        self._import_rows()
        self._import_columns()
        self._import_widgets()
        self._import_status_updates()
        self._import_notifications()
        self._import_polls()
        self._import_poll_choices()
        self._import_site_access_requests()
        self._import_site_invitations()
        self._import_group_invitations()

        # All done!
        self.stdout.write("\n>> Done!")

    def _import_settings(self):
        self.stdout.write("\n>> Settings (x) ", ending="")
        close_old_connections()
        elgg_site = ElggSitesEntity.objects.using(self.import_id).first()

        whitelisted_domains = []
        if self.helpers.get_plugin_setting("domain_whitelist", "pleio"):
            for domain in self.helpers.get_plugin_setting("domain_whitelist", "pleio").split(','):
                if is_valid_domain(domain.strip()):
                    whitelisted_domains.append(domain.strip())

        initiative_image = self.helpers.get_plugin_setting("initiative_image")
        if not initiative_image:
            initiative_image = self.helpers.save_and_get_site_logo_or_icon(elgg_site, 'logo')

        config.REDIRECTS = self.helpers.get_rewrites()
        config.NAME = html.unescape(elgg_site.name)
        config.SUBTITLE = html.unescape(elgg_site.description)
        config.THEME = self.helpers.get_plugin_setting("theme")
        config.ACHIEVEMENTS_ENABLED = self.helpers.get_plugin_setting("achievements_enabled") == "yes"
        config.CANCEL_MEMBERSHIP_ENABLED = self.helpers.get_plugin_setting("cancel_membership_enabled") == "yes"
        try:
            config.DEFAULT_ACCESS_ID = int(self.helpers.get_site_config('default_access'))
            if config.DEFAULT_ACCESS_ID not in [0,1,2]:
                config.DEFAULT_ACCESS_ID = 1
        except ValueError:
            config.DEFAULT_ACCESS_ID = 1
        config.LANGUAGE = self.helpers.get_site_config('language') if self.helpers.get_site_config('language') else "nl"
        config.LOGO = self.helpers.save_and_get_site_logo_or_icon(elgg_site, 'logo')
        config.LOGO_ALT = html.unescape(self.helpers.get_plugin_setting("logo_alt")) \
            if self.helpers.get_plugin_setting("logo_alt") else ""
        config.ICON = self.helpers.save_and_get_site_logo_or_icon(elgg_site, 'icon')
        config.ICON_ALT = html.unescape(self.helpers.get_plugin_setting("icon_alt")) \
            if self.helpers.get_plugin_setting("icon_alt") else ""
        config.ICON_ENABLED = self.helpers.get_plugin_setting("show_icon") == "yes"
        config.STARTPAGE = self.helpers.get_plugin_setting("startpage") # TODO: what if CMS page, convert to guid?
        config.LEADER_ENABLED = self.helpers.get_plugin_setting("show_leader") == "yes"
        config.LEADER_BUTTONS_ENABLED = self.helpers.get_plugin_setting("show_leader_buttons") == "yes"
        config.LEADER_IMAGE = self.helpers.get_plugin_setting("leader_image") # TODO: convert URL ?
        config.INITIATIVE_ENABLED = self.helpers.get_plugin_setting("show_initiative") == "yes"
        config.INITIATIVE_TITLE = html.unescape(self.helpers.get_plugin_setting("initiative_title")) \
            if self.helpers.get_plugin_setting("initiative_title") else ""
        config.INITIATIVE_IMAGE = initiative_image
        config.INITIATIVE_IMAGE_ALT = html.unescape(self.helpers.get_plugin_setting("initiative_image_alt")) \
            if self.helpers.get_plugin_setting("initiative_image_alt") else ""
        config.INITIATIVE_DESCRIPTION = html.unescape(self.helpers.get_plugin_setting("initiative_description")) \
            if self.helpers.get_plugin_setting("initiative_description") else ""
        config.INITIATIVE_LINK = self.helpers.get_plugin_setting("initiator_link")

        config.FONT = self.helpers.get_plugin_setting("font")
        config.COLOR_PRIMARY = self.helpers.get_plugin_setting("color_primary")
        config.COLOR_SECONDARY = self.helpers.get_plugin_setting("color_secondary")
        config.COLOR_HEADER = self.helpers.get_plugin_setting("color_header")
        config.CUSTOM_TAGS_ENABLED = self.helpers.get_plugin_setting("custom_tags_allowed") == "yes"
        config.TAG_CATEGORIES = json.loads(html.unescape(self.helpers.get_plugin_setting("tagCategories"))) \
            if self.helpers.get_plugin_setting("tagCategories") else []
        config.SHOW_TAGS_IN_FEED = self.helpers.get_plugin_setting("show_tags_in_feed") == "yes"
        config.SHOW_TAGS_IN_DETAIL = self.helpers.get_plugin_setting("show_tags_in_detail") == "yes"
        config.ACTIVITY_FEED_FILTERS_ENABLED = self.helpers.get_plugin_setting("show_extra_homepage_filters") == "yes"
        config.MENU = self.helpers.get_menu(json.loads(html.unescape(self.helpers.get_plugin_setting("menu")))) \
            if self.helpers.get_plugin_setting("menu") else []
        config.FOOTER = json.loads(html.unescape(self.helpers.get_plugin_setting("footer"))) \
            if self.helpers.get_plugin_setting("footer") else []
        config.DIRECT_LINKS = json.loads(html.unescape(self.helpers.get_plugin_setting("directLinks"))) \
            if self.helpers.get_plugin_setting("directLinks") else []
        config.SHOW_LOGIN_REGISTER = self.helpers.get_plugin_setting("show_login_register") == "yes"
        config.SUBGROUPS = self.helpers.get_plugin_setting("subgroups") == "yes"
        config.DESCRIPTION = html.unescape(elgg_site.description) \
            if elgg_site.description else ""
        config.IS_CLOSED = self.helpers.get_site_config('walled_garden')
        config.LOGIN_INTRO = self.helpers.get_plugin_setting("walled_garden_description", "pleio") \
            if self.helpers.get_plugin_setting("walled_garden_description", "pleio") else ""
        config.ALLOW_REGISTRATION = self.helpers.get_site_config('allow_registration')
        config.DIRECT_REGISTRATION_DOMAINS = whitelisted_domains
        config.GOOGLE_ANALYTICS_ID = html.unescape(self.helpers.get_plugin_setting("google_analytics")) \
            if self.helpers.get_plugin_setting("google_analytics") else ""
        config.GOOGLE_SITE_VERIFICATION = html.unescape(self.helpers.get_plugin_setting("google_site_verification")) \
            if self.helpers.get_plugin_setting("google_site_verification") else ""
        config.PIWIK_URL = html.unescape(self.helpers.get_plugin_setting("piwik_url")) \
            if self.helpers.get_plugin_setting("piwik_url") else ""
        config.PIWIK_ID = html.unescape(self.helpers.get_plugin_setting("piwik")) \
            if self.helpers.get_plugin_setting("piwik") else ""

        config.LIKE_ICON = self.helpers.get_plugin_setting("like_icon") \
            if self.helpers.get_plugin_setting("like_icon") == "thumbs" else "heart"

        config.NUMBER_OF_FEATURED_ITEMS = self.helpers.get_plugin_setting("number_of_featured_items")
        config.ENABLE_FEED_SORTING = self.helpers.get_plugin_setting("enable_feed_sorting") == "yes"
        config.SUBTITLE = html.unescape(self.helpers.get_plugin_setting("subtitle")) \
            if self.helpers.get_plugin_setting("subtitle") else ""
        config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY = html.unescape(self.helpers.get_plugin_setting("default_email_overview")) \
            if self.helpers.get_plugin_setting("default_email_overview") else ""
        config.EMAIL_OVERVIEW_SUBJECT = html.unescape(self.helpers.get_plugin_setting("email_overview_subject")) \
            if self.helpers.get_plugin_setting("email_overview_subject") else ""
        config.EMAIL_OVERVIEW_TITLE = html.unescape(self.helpers.get_plugin_setting("email_overview_title")) \
            if self.helpers.get_plugin_setting("email_overview_title") else ""
        config.EMAIL_OVERVIEW_INTRO = html.unescape(self.helpers.get_plugin_setting("email_overview_intro")) \
            if self.helpers.get_plugin_setting("email_overview_intro") else ""
        config.EMAIL_OVERVIEW_ENABLE_FEATURED = self.helpers.get_plugin_setting("email_overview_enable_featured") == "yes"
        config.EMAIL_OVERVIEW_FEATURED_TITLE = html.unescape(self.helpers.get_plugin_setting("email_overview_featured_title")) \
            if self.helpers.get_plugin_setting("email_overview_featured_title") else ""
        config.EMAIL_NOTIFICATION_SHOW_EXCERPT = self.helpers.get_plugin_setting("email_notification_show_excerpt") == "yes"
        config.SHOW_UP_DOWN_VOTING = self.helpers.get_plugin_setting("enable_up_down_voting") == "yes"
        config.ENABLE_SHARING = self.helpers.get_plugin_setting("enable_sharing") == "yes"
        config.SHOW_VIEW_COUNT = self.helpers.get_plugin_setting("enable_views_count") == "yes"
        config.NEWSLETTER = self.helpers.get_plugin_setting("newsletter") == "yes"
        config.CANCEL_MEMBERSHIP_ENABLED = self.helpers.get_plugin_setting("cancel_membership_enabled") == "yes"
        config.COMMENT_ON_NEWS = self.helpers.get_plugin_setting("comments_on_news") == "yes"
        config.EVENT_EXPORT = self.helpers.get_plugin_setting("event_export") == "yes"
        config.QUESTIONER_CAN_CHOOSE_BEST_ANSWER = self.helpers.get_plugin_setting("questioner_can_choose_best_answer") == "yes"
        config.STATUS_UPDATE_GROUPS = self.helpers.get_plugin_setting("status_update_groups") == "yes"
        config.GROUP_MEMBER_EXPORT = self.helpers.get_plugin_setting("member_export") == "yes"
        config.LIMITED_GROUP_ADD = self.helpers.get_plugin_setting("limited_groups", "groups") == "yes"
        config.ENABLE_SEARCH_ENGINE_INDEXING = self.helpers.get_site_config('enable_frontpage_indexing') \
            if self.helpers.get_site_config('enable_frontpage_indexing') else False
        config.CUSTOM_CSS = self.helpers.get_plugin_setting("custom_css", "custom_css") \
            if self.helpers.get_plugin_setting("custom_css", "custom_css") else ""
        config.WHITELISTED_IP_RANGES = self.helpers.get_plugin_setting("allowed_ip", "walled_garden_by_ip").split('\r\n') \
            if self.helpers.get_plugin_setting("allowed_ip", "walled_garden_by_ip") else []
        config.COOKIE_CONSENT = self.helpers.is_plugin_active('cookie_consent')
        config.SHOW_EXCERPT_IN_NEWS_CARD = self.helpers.get_plugin_setting("show_excerpt_in_news_card") == "yes"
        config.IDP_ID = self.helpers.get_plugin_setting("idp", "pleio") \
            if self.helpers.get_plugin_setting("idp", "pleio") else ""
        config.IDP_NAME = self.helpers.get_plugin_setting("idp_name", "pleio") \
            if self.helpers.get_plugin_setting("idp_name", "pleio") else ""

        # if plugin walled_garde_by_ip is active, the site is closed
        if self.helpers.is_plugin_active('walled_garden_by_ip'):
            config.IS_CLOSED = True

        self.stdout.write(".", ending="")

    def _import_groups(self):
        close_old_connections()
        elgg_groups = ElggGroupsEntity.objects.using(self.import_id)

        self.stdout.write("\n>> Groups (%i) " % elgg_groups.count(), ending="")

        for elgg_group in elgg_groups:

            group = self.mapper.get_group(elgg_group)
            group.save()

            # first add members
            relations = elgg_group.entity.relation_inverse.filter(relationship="member", left__type='user')
            for relation in relations:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)
                except ObjectDoesNotExist:
                    continue

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
                        'enable_notification': enabled_notifications,
                        'created_at': datetime.fromtimestamp(relation.time_created)
                    }
                )

            # then update or add admins
            relations = elgg_group.entity.relation_inverse.filter(relationship="group_admin", left__type='user')
            for relation in relations:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)
                except ObjectDoesNotExist:
                    continue

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
                        'enable_notification': enabled_notifications,
                        'created_at': datetime.fromtimestamp(relation.time_created)
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
                    'enable_notification': enabled_notifications,
                    'created_at': datetime.fromtimestamp(elgg_group.entity.time_created)
                }
            )

            relations = elgg_group.entity.relation_inverse.filter(relationship="membership_request")
            for relation in relations:
                try:
                    user = User.objects.get(id=GuidMap.objects.get(id=relation.left.guid).guid)
                except ObjectDoesNotExist:
                    continue
                # try creating pending member, if already exists, then continue
                try:
                    group.members.create(
                        user=user,
                        type='pending',
                        created_at=datetime.fromtimestamp(relation.time_created)
                    )
                except Exception:
                    continue

            access_collections = ElggAccessCollections.objects.using(self.import_id).filter(owner_guid=elgg_group.entity.guid)
            for item in access_collections:
                if not item.name[:6] in ['Groep:', 'Group:']:
                    self.mapper.save_subgroup(item, group)

            GuidMap.objects.create(id=elgg_group.entity.guid, guid=group.guid, object_type='group')

            self.stdout.write(".", ending="")

    def _import_profile_fields(self):
        close_old_connections()

        # Import site profile settings
        pleio_template_profile = self.helpers.get_plugin_setting("profile")

        # Store fields for later use
        profile_fields = []

        if pleio_template_profile:
            profile_items = json.loads(pleio_template_profile)
        else:
            profile_items = []

        # merge with "hidden" profile items
        profile_field_entities = ElggEntities.objects.using(self.import_id).filter(
            subtype__subtype="custom_profile_field"
        )

        # check if profiel field is already in profile_items else add
        for item in profile_field_entities:
            key = item.get_metadata_value_by_name('metadata_name')
            name = item.get_metadata_value_by_name('metadata_label')
            found = pydash.find(profile_items, lambda o: o.get('key', False) == key)
            if not found:
                profile_items.append({
                    'key': key,
                    'name': name
                })

        self.stdout.write("\n>> ProfileItems (%i) " % len(profile_items), ending="")
        for item in profile_items:

            profile_field = self.mapper.get_profile_field(item)
            profile_field.save()
            profile_fields.append(profile_field)

            self.stdout.write(".", ending="")

        if pleio_template_profile:
            config.PROFILE_SECTIONS = self.helpers.get_profile_sections(json.loads(html.unescape(pleio_template_profile)))

        # if one of the profile_fields is_mandatory enable onboarding form
        mandatory_fields = ProfileField.objects.filter(is_mandatory=True).first()
        if mandatory_fields:
            config.ONBOARDING_ENABLED = True
            # Only enforce when plugin setting enforce_completion_mandatory_fields is yes
            config.ONBOARDING_FORCE_EXISTING_USERS = self.helpers.get_plugin_setting('enforce_completion_mandatory_fields', 'profile_manager') == 'yes'

        return profile_fields

    def _import_users(self):
        close_old_connections()

        # get profile fields
        profile_fields = self._import_profile_fields()

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
        close_old_connections()
        elgg_blogs = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='blog')

        self.stdout.write("\n>> Blogs (%i) " % elgg_blogs.count(), ending="")

        for elgg_blog in elgg_blogs:
            blog = self.mapper.get_blog(elgg_blog)

            try:
                blog.save()
                self.helpers.save_entity_annotations(elgg_blog, blog)
                self._import_comments_for(blog, elgg_blog.entity.guid)

                GuidMap.objects.create(id=elgg_blog.entity.guid, guid=blog.guid, object_type='blog')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_news(self):
        close_old_connections()
        elgg_news_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='news')

        self.stdout.write("\n>> News (%i) " % elgg_news_items.count(), ending="")

        for elgg_news in elgg_news_items:
            news = self.mapper.get_news(elgg_news)

            try:
                news.save()
                self.helpers.save_entity_annotations(elgg_news, news)
                self._import_comments_for(news, elgg_news.entity.guid)

                GuidMap.objects.create(id=elgg_news.entity.guid, guid=news.guid, object_type='news')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_events(self):
        close_old_connections()
        elgg_event_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='event')

        self.stdout.write("\n>> Events (%i) " % elgg_event_items.count(), ending="")

        for elgg_event in elgg_event_items:
            event = self.mapper.get_event(elgg_event)

            try:
                event.save()
                self.helpers.save_entity_annotations(elgg_event, event, ["bookmark", "view_count", "views"])
                # attending
                relations = elgg_event.entity.relation.filter(relationship="event_attending", right__type='user')
                for relation in relations:
                    try:
                        user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)
                    except ObjectDoesNotExist:
                        continue

                    event.attendees.update_or_create(
                        user=user,
                        state="accept",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                # maybe
                relations = elgg_event.entity.relation.filter(relationship="event_maybe", right__type='user')
                for relation in relations:
                    try:
                        user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)
                    except ObjectDoesNotExist:
                        continue

                    event.attendees.update_or_create(
                        user=user,
                        state="maybe",
                        created_at=datetime.fromtimestamp(relation.time_created),
                        updated_at=datetime.fromtimestamp(relation.time_created)
                    )

                # reject
                relations = elgg_event.entity.relation.filter(relationship="event_reject", right__type='user')
                for relation in relations:
                    try:
                        user = User.objects.get(id=GuidMap.objects.get(id=relation.right.guid).guid)
                    except ObjectDoesNotExist:
                        continue

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
        close_old_connections()
        elgg_discussion_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='discussion')

        self.stdout.write("\n>> Discussions (%i) " % elgg_discussion_items.count(), ending="")

        for elgg_discussion in elgg_discussion_items:
            discussion = self.mapper.get_discussion(elgg_discussion)

            try:
                discussion.save()
                self.helpers.save_entity_annotations(elgg_discussion, discussion)
                self._import_comments_for(discussion, elgg_discussion.entity.guid)

                GuidMap.objects.create(id=elgg_discussion.entity.guid, guid=discussion.guid, object_type='discussion')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_questions(self):
        close_old_connections()
        elgg_question_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='question')

        self.stdout.write("\n>> Questions (%i) " % elgg_question_items.count(), ending="")

        for elgg_question in elgg_question_items:
            question = self.mapper.get_question(elgg_question)

            try:

                question.save()

                self.helpers.save_entity_annotations(elgg_question, question)
                self._import_comments_for(question, elgg_question.entity.guid, elgg_question.entity)

                GuidMap.objects.create(id=elgg_question.entity.guid, guid=question.guid, object_type='question')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_tasks(self):
        close_old_connections()
        elgg_task_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='task')

        self.stdout.write("\n>> Tasks (%i) " % elgg_task_items.count(), ending="")

        for elgg_task in elgg_task_items:
            task = self.mapper.get_task(elgg_task)

            try:
                task.save()

                self._import_comments_for(task, elgg_task.entity.guid)

                GuidMap.objects.create(id=elgg_task.entity.guid, guid=task.guid, object_type='task')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_pages(self):
        close_old_connections()
        elgg_page_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='page')

        self.stdout.write("\n>> Pages (%i) " % elgg_page_items.count(), ending="")

        for elgg_page in elgg_page_items:
            page = self.mapper.get_page(elgg_page)

            try:
                page.save()

                GuidMap.objects.create(id=elgg_page.entity.guid, guid=page.guid, object_type='page')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

        # add parent pages
        close_old_connections()
        elgg_page_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='page')

        for elgg_page in elgg_page_items:
            self.helpers.save_parent_page(elgg_page)

        config_cms_page = self.helpers.get_plugin_setting("startpage_cms")

        if config_cms_page and int(config_cms_page) > 0:
            cms_page_guid = GuidMap.objects.get(id=int(config_cms_page)).guid
            config.STARTPAGE_CMS = str(cms_page_guid)

    def _import_rows(self):
        close_old_connections()
        elgg_row_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='row')

        self.stdout.write("\n>> Rows (%i) " % elgg_row_items.count(), ending="")

        for elgg_row in elgg_row_items:
            row = self.mapper.get_row(elgg_row)
            if row:
                try:
                    row.save()

                    GuidMap.objects.create(id=elgg_row.entity.guid, guid=row.guid, object_type='row')

                    self.stdout.write(".", ending="")
                except IntegrityError as e:
                    self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                    pass
            else:
                self.stdout.write("x", ending="")

    def _import_columns(self):
        close_old_connections()
        elgg_column_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='column')

        self.stdout.write("\n>> Columns (%i) " % elgg_column_items.count(), ending="")

        for elgg_column in elgg_column_items:
            column = self.mapper.get_column(elgg_column)
            if column:
                try:
                    column.save()

                    GuidMap.objects.create(id=elgg_column.entity.guid, guid=column.guid, object_type='column')

                    self.stdout.write(".", ending="")
                except IntegrityError as e:
                    self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                    pass
            else:
                self.stdout.write("x", ending="")

    def _import_widgets(self):
        close_old_connections()
        elgg_widget_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='page_widget')

        self.stdout.write("\n>> Widgets (%i) " % elgg_widget_items.count(), ending="")

        for elgg_widget in elgg_widget_items:
            widget = self.mapper.get_widget(elgg_widget)

            try:
                widget.save()

                GuidMap.objects.create(id=elgg_widget.entity.guid, guid=widget.guid, object_type='widget')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_status_updates(self):
        close_old_connections()
        elgg_status_update_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='thewire')

        self.stdout.write("\n>> StatusUpdates (%i) " % elgg_status_update_items.count(), ending="")

        for elgg_status_update in elgg_status_update_items:
            status_update = self.mapper.get_status_update(elgg_status_update)

            try:
                status_update.save()
                self.helpers.save_entity_annotations(elgg_status_update, status_update)

                self._import_comments_for(status_update, elgg_status_update.entity.guid)

                GuidMap.objects.create(id=elgg_status_update.entity.guid, guid=status_update.guid, object_type='status_update')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_polls(self):
        close_old_connections()
        elgg_poll_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='poll')

        self.stdout.write("\n>> Polls (%i) " % elgg_poll_items.count(), ending="")

        for elgg_poll in elgg_poll_items:
            poll = self.mapper.get_poll(elgg_poll)

            try:
                poll.save()

                GuidMap.objects.create(id=elgg_poll.entity.guid, guid=poll.guid, object_type='poll')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_poll_choices(self):
        close_old_connections()
        elgg_poll_choice_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='poll_choice')

        self.stdout.write("\n>> Poll choices (%i) " % elgg_poll_choice_items.count(), ending="")

        for elgg_poll_choice in elgg_poll_choice_items:
            poll_choice = self.mapper.get_poll_choice(elgg_poll_choice)

            try:
                if poll_choice:
                    poll_choice.save()

                    # import the votes
                    elgg_poll_entity = ElggEntities.objects.using(self.import_id).get(
                        guid=GuidMap.objects.get(guid=poll_choice.poll.guid, object_type="poll").id
                    )
                    name_id = ElggMetastrings.objects.using(self.import_id).filter(string="vote").first().id
                    value_id = ElggMetastrings.objects.using(self.import_id).filter(string=poll_choice.text).first().id

                    for vote in ElggAnnotations.objects.using(self.import_id).filter(entity=elgg_poll_entity, name_id=name_id, value_id=value_id):
                        user = User.objects.get(id=GuidMap.objects.get(id=vote.owner_guid, object_type="user").guid)
                        poll_choice.add_vote(user, 1)

                    self.stdout.write(".", ending="")
                else:
                    self.stdout.write("x", ending="")
            except Exception as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_notifications(self):
        close_old_connections()
        elgg_notification_items = ElggNotifications.objects.using(self.import_id)

        self.stdout.write("\n>> Notifications (%i) " % elgg_notification_items.count(), ending="")

        for elgg_notification in elgg_notification_items:
            notification = self.mapper.get_notification(elgg_notification)

            try:
                if notification:
                    notification.save()
                    self.stdout.write(".", ending="")
                else:
                    self.stdout.write("x", ending="")
            except Exception as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_file_folders(self):
        close_old_connections()
        elgg_folder_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='folder')

        self.stdout.write("\n>> File folders (%i) " % elgg_folder_items.count(), ending="")

        for elgg_folder in elgg_folder_items:
            folder = self.mapper.get_folder(elgg_folder)

            try:
                if folder:
                    folder.save()

                    GuidMap.objects.create(id=elgg_folder.entity.guid, guid=folder.guid, object_type='folder')

                    self.stdout.write(".", ending="")
                else:
                    self.stdout.write("x", ending="")

            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

        close_old_connections()

        for folder in FileFolder.objects.all():
            try:
                elgg_folder_id = GuidMap.objects.get(guid=folder.guid, object_type='folder').id
                elgg_folder = ElggObjectsEntity.objects.using(self.import_id).filter(entity__guid=elgg_folder_id, entity__subtype__subtype='folder').first()
                parent_id = elgg_folder.entity.get_metadata_value_by_name("parent_guid")
                if parent_id and int(parent_id) > 0:
                    guid_map_parent = GuidMap.objects.get(id=parent_id, object_type='folder')
                    parent_folder = FileFolder.objects.get(id=guid_map_parent.guid)
                    folder.parent = parent_folder
                    folder.save()
            except ObjectDoesNotExist:
                self.stdout.write("x", ending="")

    def _import_files(self):
        close_old_connections()
        elgg_file_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='file')

        self.stdout.write("\n>> Files (%i) " % elgg_file_items.count(), ending="")

        for elgg_file in elgg_file_items:
            file = self.mapper.get_file(elgg_file)

            if not file:
                self.stdout.write("x", ending="")
                continue

            try:
                file.save()

                GuidMap.objects.create(id=elgg_file.entity.guid, guid=file.guid, object_type='file')

                self.stdout.write(".", ending="")
            except Exception as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

    def _import_comments_for(self, entity: Entity, elgg_guid, elgg_entity=None):
        elgg_comment_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='comment', entity__container_guid=elgg_guid)

        for elgg_comment in elgg_comment_items:
            comment = self.mapper.get_comment(elgg_comment)

            try:
                comment.container = entity
                comment.save()

                self.helpers.save_entity_annotations(elgg_comment, comment, ["vote"])

                GuidMap.objects.create(id=elgg_comment.entity.guid, guid=comment.guid, object_type='comment')
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

            # question needs comment to be created before save
            if entity.type_to_string == 'question':
                self.helpers.save_best_answer(entity, comment, elgg_entity)

    def _import_wikis(self):
        close_old_connections()
        elgg_wiki_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='wiki')

        self.stdout.write("\n>> Wikis (%i) " % elgg_wiki_items.count(), ending="")

        for elgg_wiki in elgg_wiki_items:
            wiki = self.mapper.get_wiki(elgg_wiki)

            try:
                wiki.save()

                GuidMap.objects.create(id=elgg_wiki.entity.guid, guid=wiki.guid, object_type='wiki')

                self.stdout.write(".", ending="")
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("Error: %s\n" % str(e)))
                pass

        # add parent wikis
        close_old_connections()
        elgg_wiki_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='wiki')

        for elgg_wiki in elgg_wiki_items:
            self.helpers.save_parent_wiki(elgg_wiki)

        # Fix wiki children group + ACL
        wikis = Wiki.objects.filter(parent=None).exclude(group=None)
        for wiki in wikis:
            self.helpers.update_wiki_children_acl(wiki)

    def _import_site_access_requests(self):
        close_old_connections()
        elgg_site_access_requests = PleioRequestAccess.objects.using(self.import_id).all()

        self.stdout.write("\n>> Site access requests (%i) " % elgg_site_access_requests.count(), ending="")

        for request in elgg_site_access_requests:
            value = bytes(request.user.encode())
            user = unserialize(value, decode_strings=True)
            try:
                sub = user['guid']
                email = user['email']
                name = user['name']
                claims = {"sub": sub, "email": email, "name": name}
                SiteAccessRequest.objects.create(
                    name=name,
                    email=email,
                    claims=claims
                )
                self.stdout.write(".", ending="")
            except Exception:
                self.stdout.write("x", ending="")

    def _import_site_invitations(self):
        close_old_connections()

        try:
            name_id = ElggMetastrings.objects.using(self.import_id).filter(string="site_invitation").first().id
            elgg_site_invitations = ElggAnnotations.objects.using(self.import_id).filter(name_id=name_id)
        except Exception:
            elgg_site_invitations = ElggAnnotations.objects.none()

        self.stdout.write("\n>> Site invitations (%i) " % elgg_site_invitations.count(), ending="")

        for invite in elgg_site_invitations:
            try:
                value = ElggMetastrings.objects.using(self.import_id).filter(id=invite.value_id).first().string
                values = value.split("|")
                SiteInvitation.objects.create(
                    email=values[1],
                    code=values[0]
                )
                self.stdout.write(".", ending="")
            except Exception:
                self.stdout.write("x", ending="")

    def _import_group_invitations(self):
        close_old_connections()

        try:
            name_id = ElggMetastrings.objects.using(self.import_id).filter(string="email_invitation").first().id
            elgg_group_invitations = ElggAnnotations.objects.using(self.import_id).filter(name_id=name_id)
        except Exception:
            elgg_group_invitations = ElggAnnotations.objects.none()

        self.stdout.write("\n>> Group invitations (%i) " % elgg_group_invitations.count(), ending="")

        for invite in elgg_group_invitations:
            try:
                value = ElggMetastrings.objects.using(self.import_id).filter(id=invite.value_id).first().string
                values = value.split("|")
                group = Group.objects.get(id=GuidMap.objects.get(id=invite.entity.guid).guid)
                user = User.objects.get(email=values[1])
                GroupInvitation.objects.create(
                    group=group,
                    invited_user=user,
                    code=values[0]
                )
                self.stdout.write(".", ending="")
            except Exception:
                self.stdout.write("x", ending="")

    def debug_model(self, model):
        self.stdout.write(', '.join("%s: %s" % item for item in vars(model).items() if not item[0].startswith('_')))
