from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, USER_NOT_MEMBER_OF_GROUP, LEAVING_GROUP_IS_DISABLED
from core.lib import clean_graphql_input

def resolve_leave_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if group.is_leaving_group_disabled:
        raise GraphQLError(LEAVING_GROUP_IS_DISABLED)

    if not group.is_member(user):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    group.leave(user)

    return {
        "group": group
    }
