from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import Group
from user.models import User
from core.lib import remove_none_from_dict

def resolve_edit_group_notifications(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if clean_input.get('userGuid'):
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

    if not requested_user == user and not user.is_admin:
        raise GraphQLError(COULD_NOT_SAVE)
    
    group.getsNotifications = None
    if 'getsNotifications' in clean_input:
        group.set_member_notification(requested_user, clean_input['getsNotifications'])
        group.getsNotifications = clean_input['getsNotifications']
    
    return {
        "group": group
    }
