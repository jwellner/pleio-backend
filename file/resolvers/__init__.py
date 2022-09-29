from ariadne import ObjectType, InterfaceType
from .filefolder import filefolder
from .mutation import mutation_resolver
from .query import query

resolvers = [filefolder, mutation_resolver, query]
