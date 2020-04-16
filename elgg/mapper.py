from datetime import datetime
from user.models import User
from core.models import UserProfile, UserProfileField, ProfileField, Group, Comment
from blog.models import Blog
from news.models import News
from event.models import Event
from discussion.models import Discussion
from question.models import Question
from core.lib import ACCESS_TYPE, access_id_to_acl
from elgg.models import ElggUsersEntity, ElggSitesEntity, ElggGroupsEntity, ElggObjectsEntity, GuidMap
from elgg.helpers import ElggHelpers

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
        user.created_at = datetime.fromtimestamp(elgg_user.entity.time_created)
        user.updated_at = datetime.fromtimestamp(elgg_user.entity.time_updated)
        user.is_active = elgg_user.banned == "no"
        return user

    def get_user_profile(self, elgg_user: ElggUsersEntity):
        last_online = datetime.fromtimestamp(elgg_user.last_action) if elgg_user.last_action > 0 else None
        interval_private = elgg_user.entity.private.filter(name__startswith="email_overview_").first()
        receive_notification_metadata = elgg_user.entity.metadata.filter(name__string="notification:method:email").first()
        receive_notification_email = receive_notification_metadata.value.string == "1" if receive_notification_metadata else False

        receive_newsletter = bool(elgg_user.entity.relation.filter(relationship="subscribed", right__guid=self.elgg_site.guid).first())

        user_profile = UserProfile()
        user_profile.last_online = last_online
        user_profile.overview_email_interval = interval_private.value if interval_private else 'weekly' # TODO: should get default for site
        user_profile.overview_email_tags = [] # Not implemented uet
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
            user_profile_field.read_access = access_id_to_acl(user, metadata.access_id)
            return user_profile_field
        return None

    def get_profile_field(self, pleio_template_profile_item):
        profile_field = ProfileField()
        profile_field.key = pleio_template_profile_item.get("key")
        profile_field.name = pleio_template_profile_item.get("name")
        profile_field.category = self.helpers.get_profile_category(pleio_template_profile_item.get("key"))
        profile_field.field_type = self.helpers.get_profile_field_type(pleio_template_profile_item.get("key"))
        profile_field.field_options = self.helpers.get_profile_options(pleio_template_profile_item.get("key"))
        profile_field.is_editable_by_user = self.helpers.get_profile_is_editable(pleio_template_profile_item.get("key"))
        profile_field.is_filter = bool(pleio_template_profile_item.get("isFilter"))
        return profile_field

    def get_group(self, elgg_group: ElggGroupsEntity):

        # metadata = elgg_group.entity.metadata.all()
        # for data in metadata:
        #    print(f"{data.name.string}: {data.value.string}")
        group = Group()
        group.name = elgg_group.name
        group.created_at = datetime.fromtimestamp(elgg_group.entity.time_created)
        group.updated_at = datetime.fromtimestamp(elgg_group.entity.time_updated)
        group.description = elgg_group.description
        group.rich_description = elgg_group.entity.get_metadata_value_by_name("richDescription")
        group.introduction = elgg_group.entity.get_metadata_value_by_name("introduction") \
            if elgg_group.entity.get_metadata_value_by_name("introduction") else ""
        group.welcome_message = elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") \
            if elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") else ""
        group.icon = '' # TODO: import files
        group.created_at = datetime.fromtimestamp(elgg_group.entity.time_created)
        group.is_featured = elgg_group.entity.get_metadata_value_by_name("isFeatured") == "1"
        # group.featured_image = '' # TODO: import files
        group.featured_video = elgg_group.entity.get_metadata_value_by_name("featuredVideo")
        group.featured_position_y = int(elgg_group.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_group.entity.get_metadata_value_by_name("featuredPositionY") else 0
        group.is_closed = elgg_group.entity.get_metadata_value_by_name("membership") == "0"
        group.is_membership_on_request = group.is_closed or elgg_group.entity.get_metadata_value_by_name("isMembershipOnRequest") == "1"
        group.is_auto_membership_enabled = elgg_group.entity.get_metadata_value_by_name("isAutoMembershipEnabled") == "1"
        group.is_leaving_group_disabled = elgg_group.entity.get_metadata_value_by_name("isLeavingGroupDisabled") == "1"
        group.auto_notification = elgg_group.entity.get_metadata_value_by_name("autoNotification:") == "1"
        group.tags = self.helpers.get_list_values(elgg_group.entity.get_metadata_value_by_name("tags"))
        group.plugins = self.helpers.get_list_values(elgg_group.entity.get_metadata_value_by_name("plugins"))

        group.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_group.entity.owner_guid).guid)

        return group

    def get_blog(self, elgg_entity: ElggObjectsEntity):
        entity = Blog()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_recommended = elgg_entity.entity.get_metadata_value_by_name("isRecommended") == "1"
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        # entity.featured_image = '' # TODO: import files
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = self.helpers.get_list_values(elgg_entity.entity.get_metadata_value_by_name("tags"))
        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

        # TODO: comments, following, bookmark (separate for all content types?)
        return entity

    def get_news(self, elgg_entity: ElggObjectsEntity):
        entity = News()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        # news.featured_image = '' # TODO: import files
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = self.helpers.get_list_values(elgg_entity.entity.get_metadata_value_by_name("tags"))
        entity.source = elgg_entity.entity.get_metadata_value_by_name("source")
        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

        # TODO: comments, following, bookmark (separate for all content types?)
        return entity

    def get_event(self, elgg_entity: ElggObjectsEntity):
        entity = Event()
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_featured = elgg_entity.entity.get_metadata_value_by_name("isFeatured") == "1"
        # news.featured_image = '' # TODO: import files
        entity.featured_video = elgg_entity.entity.get_metadata_value_by_name("featuredVideo")
        entity.featured_position_y = int(elgg_entity.entity.get_metadata_value_by_name("featuredPositionY")) \
            if elgg_entity.entity.get_metadata_value_by_name("featuredPositionY") else 0
        entity.tags = self.helpers.get_list_values(elgg_entity.entity.get_metadata_value_by_name("tags"))

        entity.start_date = datetime.fromtimestamp(int(elgg_entity.entity.get_metadata_value_by_name("start_day")))
        entity.end_date = datetime.fromtimestamp(int(elgg_entity.entity.get_metadata_value_by_name("end_ts")))
        entity.location = elgg_entity.entity.get_metadata_value_by_name("location") if elgg_entity.entity.get_metadata_value_by_name("location") else ""
        entity.external_link = elgg_entity.entity.get_metadata_value_by_name("source") if elgg_entity.entity.get_metadata_value_by_name("source") else ""
        entity.max_attendees = int(elgg_entity.entity.get_metadata_value_by_name("maxAttendees")) \
            if elgg_entity.entity.get_metadata_value_by_name("maxAttendees") else None
        entity.rsvp = elgg_entity.entity.get_metadata_value_by_name("rsvp") == "1"
        entity.attend_event_without_account = elgg_entity.entity.get_metadata_value_by_name("attend_event_without_account") == "1"

        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="group").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

        # TODO: comments, following, bookmark (separate for all content types?)
        return entity

    def get_discussion(self, elgg_entity: ElggObjectsEntity):
        entity = Discussion()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.tags = self.helpers.get_list_values(elgg_entity.entity.get_metadata_value_by_name("tags"))

        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="discussion").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_question(self, elgg_entity: ElggObjectsEntity):
        entity = Question()
        entity.title = elgg_entity.title
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.is_closed = elgg_entity.entity.get_metadata_value_by_name("isClosed") == "1"

        entity.tags = self.helpers.get_list_values(elgg_entity.entity.get_metadata_value_by_name("tags"))

        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)

        in_group = GuidMap.objects.filter(id=elgg_entity.entity.container_guid, object_type="question").first()
        if in_group:
            entity.group = Group.objects.get(id=in_group.guid)

        entity.write_access = [ACCESS_TYPE.user.format(entity.owner.guid)]
        entity.read_access = access_id_to_acl(entity.owner, elgg_entity.entity.access_id)

        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity

    def get_comment(self, elgg_entity: ElggObjectsEntity):
        entity = Comment()
        entity.description = elgg_entity.description
        entity.rich_description = elgg_entity.entity.get_metadata_value_by_name("richDescription")
        entity.owner = User.objects.get(id=GuidMap.objects.get(id=elgg_entity.entity.owner_guid).guid)
        entity.created_at = datetime.fromtimestamp(elgg_entity.entity.time_created)
        entity.updated_at = datetime.fromtimestamp(elgg_entity.entity.time_updated)

        return entity