from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input

def resolve_edit_users(_, info, input):
    # pylint: disable=redefined-builtin

    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)
    action = clean_input.get('action')

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

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
                user.ban_reason = "Banned by admin"
                user.save()
        elif action == 'unban':
            for user in users:
                user.is_active = True
                user.ban_reason = ""
                user.save()

    return {
        'success': True
    }
