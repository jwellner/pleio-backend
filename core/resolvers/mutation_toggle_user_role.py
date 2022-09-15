from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.user_assign_admin_for_admin import schedule_assign_admin_for_admin_mail
from core.mail_builders.user_assign_admin_for_user import schedule_assign_admin_for_user_mail
from core.mail_builders.user_revoke_admin_for_admin import schedule_revoke_admin_for_admin_mail
from core.mail_builders.user_revoke_admin_for_user import schedule_revoke_admin_for_user_mail
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input


def resolve_toggle_user_role(_, info, input):
    # pylint: disable=redefined-builtin

    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if hasattr(USER_ROLES, clean_input.get('role').upper()):
        toggle_role = getattr(USER_ROLES, clean_input.get('role').upper())
    else:
        raise GraphQLError(COULD_NOT_SAVE)

    if toggle_role in user.roles:
        user.roles.remove(toggle_role)
        user.save()

        if toggle_role == USER_ROLES.ADMIN:
            admin_users = User.objects.filter(roles__contains=['ADMIN'])

            # mail to admins to notify about removed admin
            for admin_user in admin_users:
                schedule_revoke_admin_for_admin_mail(user=user,
                                                     sender=performing_user,
                                                     admin=admin_user)

            # mail to user to notify about removed rigths
            schedule_revoke_admin_for_user_mail(user=user,
                                                sender=performing_user)
    else:
        admin_users = list(User.objects.filter(roles__contains=['ADMIN']))

        user.roles.append(toggle_role)
        user.save()

        if toggle_role == USER_ROLES.ADMIN:
            # mail to admins to notify about added admin
            for admin_user in admin_users:
                schedule_assign_admin_for_admin_mail(user=user,
                                                     admin=admin_user,
                                                     sender=performing_user)

            # mail to user to notify about added rigths
            schedule_assign_admin_for_user_mail(user=user,
                                                sender=performing_user)

    return {
        'success': True
    }
