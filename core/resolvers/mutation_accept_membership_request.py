from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input


def resolve_accept_membership_request(_, info, input):
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

    if group.is_full_member(requesting_user):
        return {
            "group": group
        }

    group.join(requesting_user, 'member')

    from core.mail_builders.group_membership_approved import submit_group_membership_approved_mail
    submit_group_membership_approved_mail(group=group, user=requesting_user)

    return {
        "group": group
    }
