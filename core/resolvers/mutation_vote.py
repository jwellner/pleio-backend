from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity, Comment
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_VALUE, ALREADY_VOTED
from core.lib import remove_none_from_dict

def resolve_vote(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if clean_input.get("score") not in [-1,1]:
        raise GraphQLError(INVALID_VALUE)

    entity = None

    try:
        entity = Entity.objects.visible(user).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        pass

    # TODO: we should refactor up/down vote vs like
    if not entity:
        try:
            entity = Comment.objects.get(id=clean_input.get("guid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    vote = entity.get_vote(user=user)

    if vote and vote.data.get("score", 0) == clean_input.get("score"):
        raise GraphQLError(ALREADY_VOTED)

    if vote:
        vote.delete()
    else:
        entity.add_vote(user=user, score=clean_input.get("score"))
        
    return {
        "object": entity
    }
