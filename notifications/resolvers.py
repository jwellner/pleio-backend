from ariadne import ObjectType

query = ObjectType("Query")

# TODO: Implement files
@query.field("notifications")
def resolve_notifications(_, info, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    return {
        'total': 0,
        'totalUnread': 0,
        'edges': [],
    }


resolvers = [query]
