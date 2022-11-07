from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_DELETE, COULD_NOT_FIND, USER_ROLES
from core.lib import clean_graphql_input
from core.mail_builders.user_delete_complete import schedule_user_delete_complete_mail
from core.resolvers import shared
from user.models import User


def resolve_delete_user(_, info, input):
    # pylint: disable=redefined-builtin
    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(performing_user)
    shared.assert_administrator(performing_user)

    try:
        user = User.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if user.is_superadmin:
        shared.assert_superadmin(performing_user)

    is_deleted_user_admin = user.has_role(USER_ROLES.ADMIN)
    user_mailinfo = user.as_mailinfo()
    user.delete()

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

    return {
        'success': True
    }
