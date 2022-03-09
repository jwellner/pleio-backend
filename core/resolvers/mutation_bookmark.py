from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import clean_graphql_input
from core.models import Entity
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

def resolve_bookmark(_, info, input):
    # pylint: disable=redefined-builtin
    # TODO: what is isFirstbookmark can we delete it?

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.visible(user).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    bookmark = entity.get_bookmark(user)

    if not clean_input.get("isAdding"):
        if bookmark:
            bookmark.delete()
    else:
        if not bookmark:
            entity.add_bookmark(user)

    isFirstBookmark = False

    return {
        "object": entity,
        "isFirstBookmark": isFirstBookmark
    }
