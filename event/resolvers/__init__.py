from .mutation import mutation
from .query import query
from .event import event
from .slot import slot

resolvers = [query, event, mutation, slot]
