from .filefolder import file, folder, filefolder
from .mutation import mutation_resolver
from .query import query

resolvers = [filefolder, file, folder, mutation_resolver, query]
