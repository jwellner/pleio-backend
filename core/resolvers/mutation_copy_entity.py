from graphql import GraphQLError
from core.lib import remove_none_from_dict
from core.constances import INVALID_SUBTYPE

from event.resolvers.mutation import resolve_copy_event

def resolve_copy_entity(_, info, input):
    # pylint: disable=redefined-builtin

    clean_input = remove_none_from_dict(input)

    if clean_input.get("subtype") == "event":
        return resolve_copy_event(_, info, input)

    raise GraphQLError(INVALID_SUBTYPE)
