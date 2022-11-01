import logging

from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.group_invite_to_group import schedule_invite_to_group_mail
from core.models import Group, GroupInvitation
from user.models import User
from core import config
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_INVITE, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import clean_graphql_input, generate_code, tenant_schema

logger = logging.getLogger(__name__)


def resolve_invite_to_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_INVITE)

    if clean_input.get("directAdd") and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    for user_input in clean_input.get("users"):
        if 'guid' in user_input:
            try:
                receiving_user = User.objects.get(id=user_input['guid'])
                email = receiving_user.email
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
        elif 'email' in user_input:
            try:
                receiving_user = User.objects.get(email=user_input['email'])
                email = receiving_user.email
            except Exception:
                receiving_user = None
                email = user_input['email']

        if clean_input.get("directAdd"):
            if not group.is_full_member(receiving_user):
                group.join(receiving_user, 'member')
            continue

        code = None

        try:
            if receiving_user:
                code = GroupInvitation.objects.get(invited_user=receiving_user, group=group).code
        except ObjectDoesNotExist:
            pass

        try:
            code = GroupInvitation.objects.get(email=email, group=group).code
        except ObjectDoesNotExist:
            pass

        if not code:
            code = generate_code()
            GroupInvitation.objects.create(code=code, invited_user=receiving_user, group=group, email=email)

        logger.info("Sending to %s", email)

        try:
            schedule_invite_to_group_mail(
                user=receiving_user,
                sender=user,
                group=group,
                language=config.LANGUAGE if not receiving_user else None,
                email=email if not receiving_user else None
            )
        except Exception as e:
            logger.error("Error while sending invite to group mail %s %s %s",
                            tenant_schema(), e.__class__, str(e))

    return {
        "group": group
    }
