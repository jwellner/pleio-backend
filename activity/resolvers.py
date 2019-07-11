from ariadne import ObjectType

query = ObjectType("Query")


@query.field("activities")
def resolve_site(*_, containerGuid=None, offset=0, limit=20, tags=None, groupFilter=None, subtypes=None, orderBy=None, orderDirection=None):
    #pylint: disable=unused-argument
    return {
        'total': 0,
        'edges': [
        ]
    }


resolvers = [query]
