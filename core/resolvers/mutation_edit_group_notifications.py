from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.models import Group
from core.lib import remove_none_from_dict
from user.models import User

def resolve_edit_group_notifications(_, info, input):
    # pylint: disable=redefined-builtin

    # TODO: refactor this to user_settings mutation

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if 'userGuid' in clean_input:
        try:
            requested_user = User.objects.get(id=clean_input.get('userGuid'))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
    else:
        requested_user = user

    try:
        group = Group.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'notificationMode' in clean_input:
        if clean_input['notificationMode'] not in ['disable', 'overview', 'direct']:
            raise GraphQLError(COULD_NOT_SAVE)

        group.set_member_notification_mode(requested_user, clean_input['notificationMode'])

    return {
        "group": group
    }
