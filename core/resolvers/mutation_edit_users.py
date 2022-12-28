from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext
from user.models import User
from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input
from core.resolvers import shared


def resolve_edit_users(_, info, input):
    # pylint: disable=redefined-builtin
    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)
    action = clean_input.get('action')

    shared.assert_authenticated(performing_user)
    shared.assert_administrator(performing_user)

    try:
        users = User.objects.filter(id__in=clean_input.get('guids'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    # can not ban yourself
    if performing_user in users:
        raise GraphQLError(COULD_NOT_SAVE)

    for user in users:
        if action == 'ban':
            for user in users:
                user.is_active = False
                user.ban_reason = gettext("Blocked by admin")
                user.save()
        elif action == 'unban':
            for user in users:
                user.is_active = True
                user.ban_reason = ""
                user.save()

    return {
        'success': True
    }
