from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.group_access_request import schedule_group_access_request_mail
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, ALREADY_MEMBER_OF_GROUP
from core.lib import clean_graphql_input


def resolve_join_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if group.is_full_member(user):
        raise GraphQLError(ALREADY_MEMBER_OF_GROUP)

    if (not group.is_closed and not group.is_membership_on_request) or group.can_write(user):
        group.join(user, 'member')
    else:
        group.join(user, 'pending')

        receiving_members = group.members.filter(type__in=['admin', 'owner'])
        for receiving_member in receiving_members:
            schedule_group_access_request_mail(user=user,
                                               receiver=receiving_member.user,
                                               group=group)

    return {
        "group": group
    }
