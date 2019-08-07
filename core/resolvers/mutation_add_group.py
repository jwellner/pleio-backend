import reversion
from graphql import GraphQLError
from core.models import Group
from core.constances import NOT_LOGGED_IN
from core.lib import remove_none_from_dict


def resolve_add_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    clean_input = remove_none_from_dict(input)

    with reversion.create_revision():
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
        group.is_featured = clean_input.get("isFeatured", False)
        group.auto_notification = clean_input.get("autoNotification", False)

        group.plugins = clean_input.get("plugins", [])
        group.tags = clean_input.get("tags", [])

        group.save()

        group.join(user, 'owner')

        reversion.set_user(user)
        reversion.set_comment("addGroup mutation")

    return {
        "group": group
    }
