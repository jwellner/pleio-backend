from graphql import GraphQLError
import reversion
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_SUBTYPE
from core.lib import get_type, get_id, remove_none_from_dict
 

def resolve_edit_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if (clean_input.get("guid")):
        subtype = get_type(clean_input.get("guid"))
        entity_id = get_id(clean_input.get("guid"))
    else:
        raise GraphQLError(COULD_NOT_FIND)

    if not subtype == "group":
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        group = Group.objects.get(id=entity_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
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

        reversion.set_user(user)
        reversion.set_comment("addGroup mutation")

    return {
        "group": group
    }