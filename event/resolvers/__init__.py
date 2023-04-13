from .mutation import mutation
from .query import query as resolve_query
from .event import event
from .slot import slot
from .range_settings import range_settings

resolvers = [resolve_query, event, mutation, slot, range_settings]
