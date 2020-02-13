from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from user.models import User
from core.lib import remove_none_from_dict

def resolve_edit_notifications(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user and not user.is_admin:
        raise GraphQLError(COULD_NOT_SAVE)

    if 'emailNotifications' in clean_input:
        requested_user.profile.receive_notification_email = clean_input.get('emailNotifications')

    if 'newsletter' in clean_input:
        requested_user.profile.receive_newsletter = clean_input.get('newsletter')

    requested_user.profile.save()

    return {
        "user": requested_user
    }
