from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_KEY
from core.lib import clean_graphql_input
from core.mail_builders.user_delete_complete import schedule_user_delete_complete_mail
from user.models import User


def resolve_handle_delete_account_request(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    performing_user = info.context["request"].user

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    clean_input = clean_graphql_input(input)

    try:
        user_to_delete = User.objects.get(id=clean_input.get("guid"), is_delete_requested=True)
    except ObjectDoesNotExist:
        raise GraphQLError(INVALID_KEY)

    accepted = clean_input.get("accept", False)

    if accepted:
        is_deleted_user_admin = user_to_delete.has_role(USER_ROLES.ADMIN)
        user_mailinfo = user_to_delete.as_mailinfo()
        user_to_delete.delete()

        # Send email to user which is deleted
        schedule_user_delete_complete_mail(
            user_info=user_mailinfo,
            receiver_info=user_mailinfo,
            sender=performing_user,
            to_admin=False
        )

        # Send email to admins if user which is deleted is also an admin
        if is_deleted_user_admin:
            admin_users = User.objects.filter(roles__contains=['ADMIN'])
            for admin_user in admin_users:
                schedule_user_delete_complete_mail(
                    user_info=user_mailinfo,
                    receiver_info=admin_user.as_mailinfo(),
                    sender=performing_user,
                    to_admin=True
                )
    else:
        user_to_delete.is_delete_requested = False
        user_to_delete.save()

    return {
        "success": True
    }
