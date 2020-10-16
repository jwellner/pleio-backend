from graphql import GraphQLError
from core.models import ProfileField
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, COULD_NOT_FIND, USER_ROLES
from core.lib import remove_none_from_dict
from django.core.exceptions import ObjectDoesNotExist

def resolve_delete_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    try:
        profile_field = ProfileField.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    profile_field.delete()

    return {
        "success": True
    }
