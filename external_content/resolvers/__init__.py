from .external_content import external_content
from .external_content_source import external_content_source, datahub_source
from .mutation import mutation
from .query import query

resolvers = [external_content,
             external_content_source, datahub_source,
             mutation, query]
