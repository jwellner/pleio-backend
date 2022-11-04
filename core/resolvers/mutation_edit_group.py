from django.core.exceptions import ObjectDoesNotExist, ValidationError
from graphql import GraphQLError

from core.constances import (COULD_NOT_FIND, COULD_NOT_SAVE,
                             INVALID_PROFILE_FIELD_GUID, NOT_LOGGED_IN,
                             USER_ROLES)
from core.lib import ACCESS_TYPE, clean_graphql_input
from core.models import Group, GroupProfileFieldSetting, ProfileField
from core.resolvers import shared
from file.models import FileFolder
from user.models import User


def resolve_edit_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=unused-variable

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'name' in clean_input:
        group.name = clean_input.get("name")

    if 'icon' in clean_input:
        icon_file = FileFolder.objects.create(
            owner=group.owner,
            upload=clean_input.get("icon"),
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(user.id)]
        )
        group.icon = icon_file

    shared.update_featured_image(group, clean_input, image_owner=user)
    shared.resolve_update_rich_description(group, clean_input)
    shared.resolve_update_tags(group, clean_input)

    if 'introduction' in clean_input:
        group.introduction = clean_input.get("introduction")
    if 'isIntroductionPublic' in clean_input:
        group.is_introduction_public = clean_input.get("isIntroductionPublic")
    if 'welcomeMessage' in clean_input:
        group.welcome_message = clean_input.get("welcomeMessage")
    if 'requiredProfileFieldsMessage' in clean_input:
        group.required_fields_message = clean_input.get("requiredProfileFieldsMessage", "")

    if 'isClosed' in clean_input:
        group.is_closed = clean_input.get("isClosed")
    if 'isMembershipOnRequest' in clean_input:
        group.is_membership_on_request = clean_input.get("isMembershipOnRequest")
    if 'autoNotification' in clean_input:
        group.auto_notification = clean_input.get("autoNotification")
    if "isSubmitUpdatesEnabled" in clean_input:
        group.is_submit_updates_enabled = clean_input.get("isSubmitUpdatesEnabled")

    if 'plugins' in clean_input:
        group.plugins = clean_input.get("plugins")

    if user.has_role(USER_ROLES.ADMIN):
        if 'isFeatured' in clean_input:
            group.is_featured = clean_input.get("isFeatured")
        if 'isLeavingGroupDisabled' in clean_input:
            group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled")
        if 'isAutoMembershipEnabled' in clean_input:
            if not group.is_auto_membership_enabled and clean_input.get("isAutoMembershipEnabled"):
                users = User.objects.filter(is_active=True)
                for u in users:
                    if not group.is_full_member(u):
                        group.join(u, 'member')

            group.is_auto_membership_enabled = clean_input.get("isAutoMembershipEnabled")

        if 'isHidden' in clean_input:
            group.is_hidden = clean_input.get("isHidden")


    if 'showMemberProfileFieldGuids' in clean_input:
        for profile_field_id in clean_input.get("showMemberProfileFieldGuids"):
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
        # disable other
        group.profile_field_settings.exclude(
            profile_field__id__in=clean_input.get("showMemberProfileFieldGuids")).update(show_field=False)

    if 'requiredProfileFieldGuids' in clean_input:
        for profile_field_id in clean_input.get("requiredProfileFieldGuids"):
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
        # disable other
        group.profile_field_settings.exclude(
            profile_field__id__in=clean_input.get("requiredProfileFieldGuids")).update(is_required=False)

    shared.update_updated_at(group)

    group.save()

    return {
        "group": group
    }
