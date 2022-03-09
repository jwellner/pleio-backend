from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Subgroup
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input

def resolve_delete_subgroup(_, info, input):
    # pylint: disable=redefined-builtin
    # TODO: alter graphql schema to make groupGuid and name required

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    id = clean_input.get("id")

    try:
        subgroup = Subgroup.objects.get(id=id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not subgroup.group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    subgroup.delete()

    return {
        "success": True
    }
