from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.models import Group
from core.lib import clean_graphql_input
from user.models import User

def resolve_edit_group_notifications(_, info, input):
    # pylint: disable=redefined-builtin

    # TODO: refactor this to user_settings mutation

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

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

    if 'isNotificationsEnabled' in clean_input:
        group.set_member_is_notifications_enabled(requested_user, clean_input['isNotificationsEnabled'])

    if 'isNotificationDirectMailEnabled' in clean_input:
        group.set_member_is_notification_direct_mail_enabled(requested_user, clean_input['isNotificationDirectMailEnabled'])

    if 'isNotificationPushEnabled' in clean_input:
        group.set_member_is_notification_push_enabled(requested_user, clean_input['isNotificationPushEnabled'])

    return {
        "group": group
    }
