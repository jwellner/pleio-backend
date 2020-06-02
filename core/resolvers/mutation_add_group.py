from graphql import GraphQLError
from core import config
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE
from core.lib import remove_none_from_dict


def resolve_add_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if config.LIMITED_GROUP_ADD and not user.is_admin:
        raise GraphQLError(COULD_NOT_SAVE)

    clean_input = remove_none_from_dict(input)

    group = Group()
    group.owner = user
    group.name = clean_input.get("name", "")
    group.icon = clean_input.get("icon", "")
    group.description = clean_input.get("description", "")
    group.rich_description = clean_input.get("richDescription", "")
    group.introduction = clean_input.get("introduction", "")
    group.welcome_message = clean_input.get("welcomeMessage", "")

    group.is_closed = clean_input.get("isClosed", False)
    group.is_membership_on_request = clean_input.get("isMembershipOnRequest", False)
    group.auto_notification = clean_input.get("autoNotification", False)

    if user.is_admin:
        group.is_featured = clean_input.get("isFeatured", False)
        group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled", False)
        group.is_auto_membership_enabled = clean_input.get("isAutoMembershipEnabled", False)

    group.plugins = clean_input.get("plugins", [])
    group.tags = clean_input.get("tags", [])

    group.save()

    group.join(user, 'owner')

    return {
        "group": group
    }
