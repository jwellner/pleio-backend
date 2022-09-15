from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.group_reject_membership import schedule_reject_membership_mail
from core.models import Group, GroupMembership
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from core.lib import clean_graphql_input


def resolve_reject_membership_request(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("groupGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        requesting_user = User.objects.get(id=clean_input.get("userGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        membership_request = GroupMembership.objects.get(user=requesting_user, group=group)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    membership_request.delete()

    schedule_reject_membership_mail(user=user,
                                    receiver=requesting_user,
                                    group=group)

    return {
        "group": group
    }
