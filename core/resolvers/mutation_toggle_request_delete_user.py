from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.user_cancel_delete_for_admin import schedule_user_cancel_delete_for_admin_mail
from core.mail_builders.user_cancel_delete_for_user import schedule_user_cancel_delete_for_user_mail
from core.mail_builders.user_request_delete_for_admin import schedule_user_request_delete_for_admin_mail
from core.mail_builders.user_request_delete_for_user import schedule_user_request_delete_for_user_mail
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input


def resolve_toggle_request_delete_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user:
        raise GraphQLError(COULD_NOT_SAVE)

    admin_users = User.objects.filter(roles__contains=['ADMIN'])
    if user.is_delete_requested:
        user.is_delete_requested = False
        user.save()

        schedule_user_cancel_delete_for_user_mail(user=user)

        # mail to admins to notify about removed admin
        for admin_user in admin_users:
            schedule_user_cancel_delete_for_admin_mail(user=user, admin=admin_user)

    else:
        user.is_delete_requested = True
        user.save()

        schedule_user_request_delete_for_user_mail(user=user)

        # mail to admins to notify about removed admin
        for admin_user in admin_users:
            schedule_user_request_delete_for_admin_mail(user=user,
                                                       admin=admin_user)

    return {
        "viewer": user
    }
