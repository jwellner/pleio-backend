from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import GroupInvitation
from core.constances import NOT_LOGGED_IN, INVALID_CODE
from core.lib import clean_graphql_input

def resolve_accept_group_invitation(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    invitation = None
    try:
        invitation = GroupInvitation.objects.get(invited_user=user, code=clean_input.get("code"))
    except ObjectDoesNotExist:
        pass

    try:
        invitation = GroupInvitation.objects.get(email=user.email, code=clean_input.get("code"))
    except ObjectDoesNotExist:
        pass

    if not invitation:
        raise GraphQLError(INVALID_CODE)

    group = invitation.group

    if not group.is_full_member(user):
        group.join(user, 'member')

    invitation.delete()

    return {
        "group": group
    }
