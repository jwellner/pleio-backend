from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES, INVALID_VALUE
from user.models import User
from core.lib import clean_graphql_input, get_language_options


def resolve_edit_notifications(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # TODO: refactor to edit user settings

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'emailNotifications' in clean_input:
        requested_user.profile.receive_notification_email = clean_input.get('emailNotifications')

    if 'isMentionNotificationsEnabled' in clean_input:
        requested_user.profile.is_mention_notifications_enabled = clean_input.get('isMentionNotificationsEnabled')

    if 'isMentionNotificationPushEnabled' in clean_input:
        requested_user.profile.is_mention_notification_push_enabled = clean_input.get('isMentionNotificationPushEnabled')

    if 'isMentionNotificationDirectMailEnabled' in clean_input:
        requested_user.profile.is_mention_notification_direct_mail_enabled = clean_input.get('isMentionNotificationDirectMailEnabled')

    if 'isCommentNotificationsEnabled' in clean_input:
        requested_user.profile.is_comment_notifications_enabled = clean_input.get('isCommentNotificationsEnabled')

    if 'isCommentNotificationPushEnabled' in clean_input:
        requested_user.profile.is_comment_notification_push_enabled = clean_input.get('isCommentNotificationPushEnabled')

    if 'isCommentNotificationDirectMailEnabled' in clean_input:
        requested_user.profile.is_comment_notification_direct_mail_enabled = clean_input.get('isCommentNotificationDirectMailEnabled')

    if 'emailNotificationsFrequency' in clean_input:
        if clean_input.get('emailNotificationsFrequency') > 0:
            requested_user.profile.notification_email_interval_hours = clean_input.get('emailNotificationsFrequency')
        else:
            raise GraphQLError(INVALID_VALUE)

    if 'newsletter' in clean_input:
        requested_user.profile.receive_newsletter = clean_input.get('newsletter')

    if 'language' in clean_input:
        if clean_input.get('language') in set((i['value'] for i in get_language_options())):
            requested_user.profile.language = clean_input.get('language')
        else:
            raise GraphQLError(INVALID_VALUE)

    requested_user.profile.save()

    return {
        "user": requested_user
    }
