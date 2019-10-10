from ariadne import ObjectType, InterfaceType
from .mutation import mutation
from .query import query
from .event import event

resolvers = [query, event, mutation]
