from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict

def resolve_join_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if (not group.is_closed and not group.is_membership_on_request) or group.can_write(user):
        group.join(user, 'member')
    else:
        group.join(user, 'pending')

    return {
        "group": group
    }
