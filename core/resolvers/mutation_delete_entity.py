from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE
from core.models import Entity, Group
from core.resolvers.mutation_delete_comment import resolve_delete_comment

def resolve_delete_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = None

    try:
        entity = Group.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        pass

    try:
        entity = Entity.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        pass

    if not entity:
        # TODO: update frontend to use deleteComment
        # raise GraphQLError(COULD_NOT_FIND)
        return resolve_delete_comment(_, info, input)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    entity.delete()

    return {
        'success': True
    }
