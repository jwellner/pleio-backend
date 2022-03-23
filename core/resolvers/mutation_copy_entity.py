from graphql import GraphQLError
from core.lib import clean_graphql_input
from core.constances import INVALID_SUBTYPE

from event.resolvers.mutation import resolve_copy_event

def resolve_copy_entity(_, info, input):
    # pylint: disable=redefined-builtin

    clean_input = clean_graphql_input(input)

    if clean_input.get("subtype") == "event":
        return resolve_copy_event(_, info, input)

    raise GraphQLError(INVALID_SUBTYPE)