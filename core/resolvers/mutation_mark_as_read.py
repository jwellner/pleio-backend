from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict


def resolve_mark_as_read(_, info, input):
    # TODO: do we wnat a mapper for notification?
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        notification = user.notifications.get(id=clean_input.get('id'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    notification.mark_as_read()
    notification.isUnread = notification.unread

    return {
          "success": True,
          "notification": notification
    }


def resolve_mark_all_as_read(_, info, input):
    # TODO: do we wnat a mapper for notification?
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        user.notifications.mark_all_as_read()
    except Exception:
        return {
            "success": False
        }      

    return {
          "success": True
    }
