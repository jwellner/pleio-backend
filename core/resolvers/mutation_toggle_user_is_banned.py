from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import remove_none_from_dict

def resolve_toggle_user_is_banned(_, info, input):
    # pylint: disable=redefined-builtin

    performing_user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    # can not ban yourself
    if performing_user.guid == user.guid:
        raise GraphQLError(COULD_NOT_SAVE)

    if user.is_active:
        user.is_active = False
        user.ban_reason = "Banned by admin"
        user.save()

    else:
        user.is_active = True
        user.ban_reason = ""
        user.save()

    return {
        'success': True
    }
