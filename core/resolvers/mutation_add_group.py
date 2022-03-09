from graphql import GraphQLError
from core import config
from core.models import Group, ProfileField, GroupProfileFieldSetting
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, USER_ROLES, INVALID_PROFILE_FIELD_GUID
from core.lib import clean_graphql_input, ACCESS_TYPE
from file.models import FileFolder
from django.core.exceptions import ValidationError


def resolve_add_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if config.LIMITED_GROUP_ADD and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    clean_input = clean_graphql_input(input)

    group = Group()
    group.owner = user
    group.name = clean_input.get("name", "")

    if 'icon' in clean_input:
        icon_file = FileFolder.objects.create(
            owner=group.owner,
            upload=clean_input.get("icon"),
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(user.id)]
        )

        group.icon = icon_file

    if 'featured' in clean_input:
        group.featured_position_y = clean_input.get("featured").get("positionY", 0)
        group.featured_video = clean_input.get("featured").get("video", "")
        group.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        group.featured_alt = clean_input.get("featured").get("alt", "")
        if group.featured_video:
            group.featured_image = None
        elif clean_input.get("featured").get("image"):

            image_file = FileFolder.objects.create(
                owner=group.owner,
                upload=clean_input.get("featured").get("image"),
                read_access=[ACCESS_TYPE.public],
                write_access=[ACCESS_TYPE.user.format(user.id)]
            )

            group.featured_image = image_file

    else:
        group.featured_image = None
        group.featured_position_y = 0
        group.featured_video = None
        group.featured_video_title = ""
        group.featured_alt = ""

    group.rich_description = clean_input.get("richDescription", "")
    group.introduction = clean_input.get("introduction", "")
    group.is_introduction_public = clean_input.get("isIntroductionPublic", False)
    group.welcome_message = clean_input.get("welcomeMessage", "")
    group.required_fields_message = clean_input.get("requiredProfileFieldsMessage", "")

    group.is_closed = clean_input.get("isClosed", False)
    group.is_hidden = clean_input.get("isHidden", False)
    group.is_membership_on_request = clean_input.get("isMembershipOnRequest", False)
    group.auto_notification = clean_input.get("autoNotification", False)

    if user.has_role(USER_ROLES.ADMIN):
        group.is_featured = clean_input.get("isFeatured", False)
        group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled", False)
        group.is_auto_membership_enabled = clean_input.get("isAutoMembershipEnabled", False)

    group.plugins = clean_input.get("plugins", [])
    group.tags = clean_input.get("tags", [])

    group.save()

    if 'showMemberProfileFieldGuids' in clean_input:
        _update_profile_field_show_field(group, clean_input.get("showMemberProfileFieldGuids"))

    if 'requiredProfileFieldGuids' in clean_input:
        _update_profile_field_required(group, clean_input.get('requiredProfileFieldGuids'))

    group.join(user, 'owner')

    return {
        "group": group
    }


def _update_profile_field_show_field(group, guids):
    for profile_field_id in guids:
        try:
            profile_field = ProfileField.objects.get(id=profile_field_id)
            setting, created = GroupProfileFieldSetting.objects.get_or_create(
                profile_field=profile_field,
                group=group
            )
            setting.show_field = True
            setting.save()
        except (ProfileField.DoesNotExist, ValidationError):
            raise GraphQLError(INVALID_PROFILE_FIELD_GUID)


def _update_profile_field_required(group, guids):
    for profile_field_id in guids:
        try:
            profile_field = ProfileField.objects.get(id=profile_field_id)
            setting, created = GroupProfileFieldSetting.objects.get_or_create(
                profile_field=profile_field,
                group=group
            )
            setting.is_required = True
            setting.save()
        except (ProfileField.DoesNotExist, ValidationError):
            raise GraphQLError(INVALID_PROFILE_FIELD_GUID)
