import graphene

class PaginatedWikiList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('wiki.nodes.WikiNode')
