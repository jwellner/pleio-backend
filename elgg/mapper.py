from datetime import datetime
from user.models import User
from core.models import UserProfile, UserProfileField, ProfileField, Group
from core.lib import ACCESS_TYPE, access_id_to_acl
from elgg.models import ElggUsersEntity, ElggSitesEntity, ElggGroupsEntity
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
        group.description = elgg_group.description
        group.rich_description = elgg_group.entity.get_metadata_value_by_name("richDescription")
        group.introduction = elgg_group.entity.get_metadata_value_by_name("introduction")
        group.welcome_message = elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") \
            if elgg_group.entity.get_private_value_by_name("group_tools:welcome_message") else ""
        group.icon = '' # TODO: import files
        group.created_at = datetime.fromtimestamp(elgg_group.entity.time_created)
        group.is_featured = elgg_group.entity.get_metadata_value_by_name("isFeatured") == "1"
        group.featured_image = '' # TODO: import files
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
        return group
