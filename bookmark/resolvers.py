from ariadne import ObjectType

query = ObjectType("Query")

# TODO: Implement files
@query.field("bookmarks")
def resolve_bookmarks(_, info, subtype=None, tags=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'canWrite': False,
        'edges': [],
    }


resolvers = [query]
