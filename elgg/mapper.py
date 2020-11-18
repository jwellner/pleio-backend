import json
import html
from datetime import datetime
from user.models import User
from core.models import UserProfile, UserProfileField, ProfileField, Group, Comment, Widget, Subgroup
from blog.models import Blog
from news.models import News
from event.models import Event
from discussion.models import Discussion
from question.models import Question
from cms.models import Page, Row, Column
from activity.models import StatusUpdate
from poll.models import Poll, PollChoice
from core.lib import ACCESS_TYPE
from notifications.models import Notification
from file.models import FileFolder
from wiki.models import Wiki
from elgg.models import (
    ElggUsersEntity, ElggSitesEntity, ElggGroupsEntity, ElggObjectsEntity, ElggPrivateSettings, GuidMap, ElggNotifications,
    ElggAccessCollections, ElggAccessCollectionMembership
)
from elgg.helpers import ElggHelpers

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import ObjectDoesNotExist
from core.constances import USER_ROLES


class Mapper():

    db = None
    elgg_site = None
    helpers = None

    def __init__(self, elgg_database):
        self.db = elgg_database
        self.helpers = ElggHelpers(self.db)
        self.elgg_site = ElggSitesEntity.objects.using(self.db).first()

    def get_user(self, elgg_user: ElggUsersEntity):
        user = User()
        user.email = elgg_user.email if elgg_user.email != '' else f'deleted@{user.guid}'
        user.name = elgg_user.name
        user.external_id = elgg_user.pleio_guid
        user.picture = f"{settings.PROFILE_PICTURE_URL}/mod/profile/icondirect.php?guid={elgg_user.pleio_guid}&size=large"
        user.created_at = datetime.fromtimestamp(elgg_user.entity.time_created)
        user.updated_at = datetime.fromtimestamp(elgg_user.entity.time_updated)
        user.is_active = elgg_user.banned == "no"
        user.ban_reason = elgg_user.entity.get_metadata_value_by_name("ban_reason") \
            if elgg_user.entity.get_metadata_value_by_name("ban_reason") and not elgg_user.banned == "no" else ""
        if elgg_user.admin == "yes":
            user.roles.append(USER_ROLES.ADMIN)
        if elgg_user.entity.relation.filter(relationship='is_subeditor').first():
            user.roles.append(USER_ROLES.EDITOR)
        if elgg_user.entity.relation.filter(relationship='questions_expert').first():
            user.roles.append(USER_ROLES.QUESTION_MANAGER)

        return user

    def get_user_profile(self, elgg_user: ElggUsersEntity):
        last_online = datetime.fromtimestamp(elgg_user.last_action) if elgg_user.last_action > 0 else None
        interval_private = elgg_user.entity.private.filter(name__startswith="email_overview_").first()
        last_received_private = elgg_user.entity.private.filter(name__startswith="latest_email_overview_").first()
        receive_notification_metadata = elgg_user.entity.metadata.filter(name__string="notification:method:email").first()
        receive_notification_email = receive_notification_metadata.value.string == "1" if receive_notification_metadata else False

        receive_newsletter = bool(elgg_user.entity.relation.filter(relationship="subscribed", right__guid=self.elgg_site.entity.guid).first())

        user_profile = UserProfile()
        user_profile.last_online = last_online
        user_profile.overview_email_interval = interval_private.value if interval_private else 'weekly' # TODO: should get default for site
        user_profile.overview_email_tags = elgg_user.entity.get_metadata_values_by_name("editEmailOverviewTags")
        user_profile.overview_email_last_received = datetime.fromtimestamp(int(last_received_private.value)) if last_received_private else None
        user_profile.receive_newsletter = receive_newsletter
        user_profile.receive_notification_email = receive_notification_email
        return user_profile

    def get_user_profile_field(self, elgg_user: ElggUsersEntity, user_profile: UserProfile, profile_field: ProfileField, user: User):
        metadata = elgg_user.entity.metadata.filter(name__string=profile_field.key).first()
        if metadata:
            user_profile_field = UserProfileField()
            user_profile_field.profile_field = profile_field
            user_profile_field.user_profile = user_profile
            user_profile_field.value = metadata.value.string
            user_profile_field.write_access = [ACCESS_TYPE.user.format(user.guid)]
            user_profile_field.read_access = self.helpers.elgg_access_id_to_acl(user, metadata.access_id)
            return user_profile_field
        return None

    def get_profile_field(self, pleio_template_profile_item):
        profile_field = ProfileField()
        profile_field.key = pleio_template_profile_item.get("key")
        profile_field.name = pleio_template_profile_item.get("name")
        profile_field.field_type = self.helpers.get_profile_field_type(pleio_template_profile_item.get("key"))
        profile_field.field_options = self.helpers.get_profile_options(pleio_template_profile_item.get("key"))
        profile_field.is_editable_by_user = self.helpers.get_profile_is_editable(pleio_template_profile_item.get("key"))
        profile_field.is_filter = bool(pleio_template_profile_item.get("isFilter"))
        profile_field.is_in_overview = bool(pleio_template_profile_item.get("isInOverview"))
        return profile_field

    def get_group(self, elgg_group: ElggGroupsEntity):

        group = Group()
        group.name = elgg_group.name
        group.created_at = datetime.fromtimestamp(elgg_group.entity.time_created)
        group.updated_at = datetime.fromtimestamp(elgg_group.entity.time_updated)
        group.description = elgg_group.description.replace("&amp;", "&")
        group.rich_description = elgg_group.entity.get_metadata_value_by_name("richDescription")
        group.introduction = elgg_group.entity.get_metadata_value_by_name("introduction") \
            if elgg_group.entity.get_metadata_value_by_name("introduction") else ""
        group.is_introduction_public = elgg_group.entity.get_metadata_value_by_name("isIntroductionPublic") == "1"
        group.welcome_message = elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") \
            if elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") else ""
        group.icon = self.helpers.save_and_get_group_icon(elgg_group)
        group.created_at = datetime.fromtimestamp(elgg_group.entity.time_created)
        group.is_featured = elgg_group.entity.get_metadata_value_by_name("isFeatured") == "1"
        group.featured_image = self.helpers.save_and_get_featured_image(elgg_group)
        group.featured_video = elgg_group.entity.get_metadata_value_by_name("featuredVideo")
        group.featured_position_y = int(elgg_group.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_group.entity.get_metadata_value_by_name("featuredPositionY") else 0
        group.is_closed = elgg_group.entity.get_metadata_value_by_name("membership") == "0"
        group.is_membership_on_request = group.is_closed or elgg_group.entity.get_metadata_value_by_name("isMembershipOnRequest") == "1"
        group.is_auto_membership_enabled = elgg_group.entity.get_metadata_value_by_name("isAutoMembershipEnabled") == "1"
        group.is_leaving_group_disabled = elgg_group.entity.get_metadata_value_by_name("isLeavingGroupDisabled") == "1"
        group.auto_notification = elgg_group.entity.get_metadata_value_by_name("autoNotification:") == "1"
        group.tags = elgg_group.entity.get_metadata_values_by_name("tags")
        group.plugins = elgg_group.entity.get_metadata_values_by_name("plugins")

        group.owner = self.helpers.get_user_or_admin(elgg_group.entity.owner_guid)

        return group

    def save_subgroup(self, elgg_access_collection: ElggAccessCollections, group):
        subgroup = Subgroup()
        subgroup.name = elgg_access_collection.name
        subgroup.group = group
        user_ids = list(ElggAccessCollectionMembership.objects.using(self.db).filter(
            access_collection_id=elgg_access_collection.id).values_list("user_guid", flat=True)
        )
        user_guids = list(GuidMap.objects.filter(id__in=user_ids, object_type="user").values_list("guid", flat=True))
        users = User.objects.filter(id__in=user_guids)
        subgroup.save()
        subgroup.members.set(users)
        return subgroup

    def get_blog(self, elgg_entity: ElggObjectsEntity):
        entity = Blog()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_recommended = elgg_entity.entity.get_metadata_value_by_name("isRecommended") == "1"
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        entity.featured_image = self.helpers.save_and_get_featured_image(elgg_entity)
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")
        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        return entity

    def get_news(self, elgg_entity: ElggObjectsEntity):
        entity = News()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        entity.featured_image = self.helpers.save_and_get_featured_image(elgg_entity)
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")
        entity.source = elgg_entity.entity.get_metadata_value_by_name("source") \
            if elgg_entity.entity.get_metadata_value_by_name("source") else ""
        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        return entity

    def get_event(self, elgg_entity: ElggObjectsEntity):
        entity = Event()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        entity.featured_image = self.helpers.save_and_get_featured_image(elgg_entity)
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.start_date = datetime.fromtimestamp(int(elgg_entity.entity.get_metadata_value_by_name("start_day")))
        entity.end_date = datetime.fromtimestamp(int(elgg_entity.entity.get_metadata_value_by_name("end_ts")))
        entity.location = elgg_entity.entity.get_metadata_value_by_name("location") if elgg_entity.entity.get_metadata_value_by_name("location") else ""
        entity.external_link = elgg_entity.entity.get_metadata_value_by_name("source") if elgg_entity.entity.get_metadata_value_by_name("source") else ""
        entity.max_attendees = int(elgg_entity.entity.get_metadata_value_by_name("maxAttendees")) \
            if elgg_entity.entity.get_metadata_value_by_name("maxAttendees") else None
        entity.rsvp = elgg_entity.entity.get_metadata_value_by_name("rsvp") == "1"
        entity.attend_event_without_account = elgg_entity.entity.get_metadata_value_by_name("attend_event_without_account") == "1"

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        return entity

    def get_discussion(self, elgg_entity: ElggObjectsEntity):
        entity = Discussion()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_question(self, elgg_entity: ElggObjectsEntity):
        entity = Question()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_closed = elgg_entity.entity.get_metadata_value_by_name("isClosed") == "1"

        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_task(self, elgg_entity: ElggObjectsEntity):
        entity = Question()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.state = elgg_entity.entity.get_metadata_value_by_name("state")

        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_page(self, elgg_entity: ElggObjectsEntity):
        entity = Page()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.page_type = elgg_entity.entity.get_metadata_value_by_name("pageType")

        entity.position = int(elgg_entity.entity.get_metadata_value_by_name("position")) \
            if elgg_entity.entity.get_metadata_value_by_name("position") else 0
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_row(self, elgg_entity: ElggObjectsEntity):
        entity = Row()
        entity.position = int(elgg_entity.entity.get_metadata_value_by_name("position")) \
            if elgg_entity.entity.get_metadata_value_by_name("position") else 0
        entity.is_full_width = elgg_entity.entity.get_metadata_value_by_name("is_full_width") == "1"

        # get the parent page
        parent_guid = elgg_entity.entity.get_metadata_value_by_name("parent_guid")
        guid_map_page = GuidMap.objects.get(id=parent_guid, object_type='page')
        entity.page = Page.objects.get(id=guid_map_page.guid)

        return entity

    def get_column(self, elgg_entity: ElggObjectsEntity):
        entity = Column()
        entity.position = int(elgg_entity.entity.get_metadata_value_by_name("position")) \
            if elgg_entity.entity.get_metadata_value_by_name("position") else 0
        entity.width = [int(elgg_entity.entity.get_metadata_value_by_name("width"))]

        # get the parent page
        guid_map_page = GuidMap.objects.get(id=elgg_entity.entity.container_guid, object_type='page')
        entity.page = Page.objects.get(id=guid_map_page.guid)

        # get the parent row
        parent_guid = elgg_entity.entity.get_metadata_value_by_name("parent_guid")
        guid_map_page = GuidMap.objects.get(id=parent_guid, object_type='row')
        entity.row = Row.objects.get(id=guid_map_page.guid)

        return entity

    def get_widget(self, elgg_entity: ElggObjectsEntity):
        entity = Widget()
        entity.position = int(elgg_entity.entity.get_metadata_value_by_name("position")) \
            if elgg_entity.entity.get_metadata_value_by_name("position") else 0
        entity.type = elgg_entity.entity.get_metadata_value_by_name("widget_type")

        try:
            has_settings = ElggPrivateSettings.objects.using(self.db).get(entity__guid=elgg_entity.entity.guid, name='settings')
            entity.settings = json.loads(html.unescape(has_settings.value))
        except Exception:
            entity.settings = []

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        in_page = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="page").first()
        if in_page:
            entity.page = Page.objects.get(id=in_page.guid)

        parent_guid = elgg_entity.entity.get_metadata_value_by_name("parent_guid")
        if parent_guid:
            in_column = GuidMap.objects.filter(id=parent_guid, object_type="column").first()
            if in_column:
                entity.column = Column.objects.get(id=in_column.guid)

        return entity

    def get_status_update(self, elgg_entity: ElggObjectsEntity):
        entity = StatusUpdate()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_comment(self, elgg_entity: ElggObjectsEntity):
        entity = Comment()
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_poll(self, elgg_entity: ElggObjectsEntity):
        entity = Poll()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_poll_choice(self, elgg_entity: ElggObjectsEntity):
        try:
            entity = PollChoice()

            elgg_poll_relation = elgg_entity.entity.relation.filter(relationship="poll_choice").first()

            if not elgg_poll_relation:
                return None

            poll_guid = GuidMap.objects.get(id=elgg_poll_relation.right.guid, object_type="poll").guid
            entity.poll = Poll.objects.get(id=poll_guid)

            entity.text = elgg_entity.entity.get_metadata_value_by_name("text")

            return entity
        except ObjectDoesNotExist:
            # Skip when old data is inconsistent
            return None


    def get_notification(self, elgg_notification: ElggNotifications):

        try:
            notification = Notification()

            notification.actor_object_id = GuidMap.objects.get(id=elgg_notification.performer_guid).guid
            notification.recipient_id = GuidMap.objects.get(id=elgg_notification.user_guid).guid
            notification.action_object_object_id = GuidMap.objects.get(id=elgg_notification.entity_guid).guid
            notification.unread = elgg_notification.unread == "yes"
            notification.verb = elgg_notification.action
            notification.actor_content_type = ContentType.objects.get(app_label='user', model='user')
            notification.timestamp = datetime.fromtimestamp(elgg_notification.time_created)
            notification.emailed = True # make sure no imported notifications are mailed again

            return notification
        except ObjectDoesNotExist:
            # Skip when old data is inconsistent
            return None

    def get_folder(self, elgg_entity: ElggObjectsEntity):
        entity = FileFolder()
        entity.title = elgg_entity.title
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

        entity.is_folder = True

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()

        entity.group = Group.objects.get(id=in_group.guid)

        write_access_id = int(elgg_entity.entity.get_metadata_value_by_name("write_access_id")) \
            if elgg_entity.entity.get_metadata_value_by_name("write_access_id") else 0

        entity.write_access = self.helpers.elgg_access_id_to_acl(entity, write_access_id)
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_file(self, elgg_entity: ElggObjectsEntity):

        try:
            entity = FileFolder()
            entity.title = elgg_entity.title
            entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")

            folder_relation = elgg_entity.entity.relation_inverse.filter(relationship="folder_of", right__guid=elgg_entity.entity.guid).first()
            if folder_relation:
                parent_guid = GuidMap.objects.get(id=folder_relation.left.guid, object_type='folder').guid
                entity.parent = FileFolder.objects.get(id=parent_guid, is_folder=True)

            entity.mime_type = str(elgg_entity.entity.get_metadata_value_by_name("mimetype"))
            entity.upload.name = self.helpers.get_elgg_file_path(elgg_entity)

            entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)

            entity.is_folder = False

            in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
            if in_group:
                entity.group = Group.objects.get(id=in_group.guid)

            write_access_id = int(elgg_entity.entity.get_metadata_value_by_name("write_access_id")) \
                if elgg_entity.entity.get_metadata_value_by_name("write_access_id") else 0

            entity.write_access = self.helpers.elgg_access_id_to_acl(entity, write_access_id)
            entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

            entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
            entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

            return entity

        except ObjectDoesNotExist:
            # Skip when old data is inconsistent
            return None

    def get_wiki(self, elgg_entity: ElggObjectsEntity):
        entity = Wiki()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description.replace("&amp;", "&")
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.tags = elgg_entity.entity.get_metadata_values_by_name("tags")
        entity.owner = self.helpers.get_user_or_admin(elgg_entity.entity.owner_guid)
        entity.position = int(elgg_entity.entity.get_metadata_value_by_name("position")) \
            if elgg_entity.entity.get_metadata_value_by_name("position") else 0

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        write_access_id = int(elgg_entity.entity.get_metadata_value_by_name("write_access_id")) \
            if elgg_entity.entity.get_metadata_value_by_name("write_access_id") else 0

        entity.write_access = self.helpers.elgg_access_id_to_acl(entity, write_access_id)
        entity.read_access = self.helpers.elgg_access_id_to_acl(entity, elgg_entity.entity.access_id)

        return entity