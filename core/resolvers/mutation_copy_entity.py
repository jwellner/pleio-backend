from graphql import GraphQLError

from cms.models import Page
from core.lib import clean_graphql_input
from core import constances
from core.constances import INVALID_SUBTYPE
from core.models import Entity
from core.utils.entity import load_entity_by_id, EntityNotFoundError
from event.models import Event
from event.resolvers.mutation_event_copy import resolve_copy_event
from cms.resolvers.mutation_copy_page import resolve_copy_page


def resolve_copy_entity(_, info, input):
    # pylint: disable=redefined-builtin
    try:
        clean_input = clean_graphql_input(input)
        entity: Entity = load_entity_by_id(clean_input.get("guid"), ['core.Entity'])
        if isinstance(entity, (Event,)):
            return resolve_copy_event(_, info, input)
        if isinstance(entity, (Page,)):
            return resolve_copy_page(_, info, input)
    except EntityNotFoundError:
        raise GraphQLError(constances.COULD_NOT_FIND)

    raise GraphQLError(INVALID_SUBTYPE)
