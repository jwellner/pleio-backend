import graphene

class PaginatedEventList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('event.nodes.EventNode')