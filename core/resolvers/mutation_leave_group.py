from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE, USER_NOT_MEMBER_OF_GROUP
from core.lib import remove_none_from_dict, get_type, get_id

def resolve_leave_group(_, info, input):
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

    if not group.is_member(user):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    group.leave(user)

    return {
        "group": group
    }
