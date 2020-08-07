from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import GroupInvitation
from core.constances import NOT_LOGGED_IN, INVALID_CODE
from core.lib import remove_none_from_dict

def resolve_accept_group_invitation(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)
    try:
        invitation = GroupInvitation.objects.get(invited_user=user, code=clean_input.get("code"))
    except ObjectDoesNotExist:
        raise GraphQLError(INVALID_CODE)

    group = invitation.group

    if not group.is_full_member(user):
        group.join(user, 'member')

    invitation.delete()

    return {
        "group": group
    }
