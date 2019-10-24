from ariadne import ObjectType, InterfaceType
from .filefolder import filefolder
from .mutation import mutation
from .query import query

resolvers = [filefolder, mutation, query]
