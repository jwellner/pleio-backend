from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import User, Group
from core.lib import remove_none_from_dict

def resolve_edit_group_notifications(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('userGuid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        group = Group.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user and not user.is_admin:
        raise GraphQLError(COULD_NOT_SAVE)
    
    group.getsNotifications = None
    if 'getsNotifications' in clean_input:
        if clean_input.get('getsNotifications'):
            try:
                requested_user.profile.group_notifications.append(clean_input.get('guid'))
                group.getsNotifications = True
            except Exception:
                pass
        else:
            try:
                requested_user.profile.group_notifications.remove(clean_input.get('guid'))
                group.getsNotifications = False
            except Exception:
                pass
    
    requested_user.profile.save()
    
    return {
        "group": group
    }
