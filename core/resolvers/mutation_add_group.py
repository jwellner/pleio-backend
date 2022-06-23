from graphql import GraphQLError
from core import config
from core.models import Group, ProfileField, GroupProfileFieldSetting
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, USER_ROLES, INVALID_PROFILE_FIELD_GUID
from core.lib import clean_graphql_input, ACCESS_TYPE
from core.resolvers import shared
from file.models import FileFolder
from django.core.exceptions import ValidationError


def resolve_add_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable

    user = info.context["request"].user

    shared.assert_authenticated(user)

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

    shared.update_featured_image(group, clean_input, image_owner=user)

    group.rich_description = clean_input.get("richDescription", "")
    group.introduction = clean_input.get("introduction", "")
    group.is_introduction_public = clean_input.get("isIntroductionPublic", False)
    group.welcome_message = clean_input.get("welcomeMessage", "")
    group.required_fields_message = clean_input.get("requiredProfileFieldsMessage", "")

    group.is_closed = clean_input.get("isClosed", False)
    group.is_hidden = clean_input.get("isHidden", False)
    group.is_membership_on_request = clean_input.get("isMembershipOnRequest", False)
    group.auto_notification = clean_input.get("autoNotification", False)
    group.is_submit_updates_enabled = clean_input.get("isSubmitUpdatesEnabled", False)

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
