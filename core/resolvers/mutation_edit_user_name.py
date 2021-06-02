from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, INVALID_VALUE, USER_ROLES
from core.lib import remove_none_from_dict
from core import config
from user.models import User

def resolve_edit_user_name(_, info, input):
    # pylint: disable=redefined-builtin
    current_user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not current_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not config.EDIT_USER_NAME_ENABLED:
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        user = User.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not current_user == user and not current_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    if not clean_input.get("name"):
        raise GraphQLError(INVALID_VALUE)

    if len(clean_input.get("name")) > 100:
        raise GraphQLError(INVALID_VALUE)

    user.name = clean_input.get("name")
    user.save()

    return {
        'user': user
    }
