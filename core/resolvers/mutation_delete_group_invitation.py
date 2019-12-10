from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import GroupInvitation
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_INVITE
from core.lib import remove_none_from_dict

def resolve_delete_group_invitation(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        invitation = GroupInvitation.objects.get(id=clean_input.get("id"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    group = invitation.group

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_INVITE)

    invitation.delete()

    return {
        "group": group
    }
