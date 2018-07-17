import graphene

class PaginatedNewsList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('news.nodes.NewsNode')
