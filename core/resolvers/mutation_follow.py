from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict

def resolve_follow(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = None

    try:
        entity = Entity.objects.visible(user).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    follow = entity.get_follow(user=user)

    if follow and not clean_input.get("isFollowing"):
        follow.delete()
    elif not follow and clean_input.get("isFollowing"):
        entity.add_follow(user=user)
        
    return {
        "object": entity
    }
