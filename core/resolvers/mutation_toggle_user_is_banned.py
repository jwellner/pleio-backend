from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.resolvers import shared
from user.models import User
from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input


def resolve_toggle_user_is_banned(_, info, input):
    # pylint: disable=redefined-builtin

    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(performing_user)
    shared.assert_administrator(performing_user)

    try:
        user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    # can not ban yourself
    shared.assert_isnt_me(user, performing_user)

    if user.is_active:
        if user.is_superadmin:
            shared.assert_superadmin(performing_user)
        user.is_active = False
        user.ban_reason = "Banned by admin"
        user.save()

    else:
        user.is_active = True
        user.ban_reason = ""
        user.save()

    return {
        'success': True
    }
