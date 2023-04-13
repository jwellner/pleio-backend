from .query import query as resolve_query
from .status_update import status_update

resolvers = [resolve_query, status_update]
