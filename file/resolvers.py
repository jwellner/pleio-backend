from ariadne import ObjectType
from core.constances import ORDER_DIRECTION, ORDER_BY

query = ObjectType("Query")

# TODO: Implement files
@query.field("files")
def resolve_files(_, info, containerGuid=None, filter=None, orderBy=ORDER_BY.timeCreated, orderDirection=ORDER_DIRECTION.asc, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    return {
        'total': 0,
        'canWrite': False,
        'edges': [],
    }


resolvers = [query]
