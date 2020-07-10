from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from core.lib import remove_none_from_dict


def resolve_edit_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches


    user = info.context.user
    clean_input = remove_none_from_dict(input)

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
        group.icon = clean_input.get("icon")
    if 'description' in clean_input:
        group.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        group.rich_description = clean_input.get("richDescription")
    if 'introduction' in clean_input:
        group.introduction = clean_input.get("introduction")
    if 'welcomeMessage' in clean_input:
        group.welcome_message = clean_input.get("welcomeMessage")

    if 'isClosed' in clean_input:
        group.is_closed = clean_input.get("isClosed")
    if 'isMembershipOnRequest' in clean_input:
        group.is_membership_on_request = clean_input.get("isMembershipOnRequest")
    if 'autoNotification' in clean_input:
        group.auto_notification = clean_input.get("autoNotification")

    if user.is_admin:
        if 'isFeatured' in clean_input:
            group.is_featured = clean_input.get("isFeatured")
        if 'isLeavingGroupDisabled' in clean_input:
            group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled")
        if 'isAutoMembershipEnabled' in clean_input:
            group.is_auto_membership_enabled = clean_input.get("isAutoMembershipEnabled")

    if 'plugins' in clean_input:
        group.plugins = clean_input.get("plugins")
    if 'tags' in clean_input:
        group.tags = clean_input.get("tags")

    group.save()

    return {
        "group": group
    }
