import graphene

class PaginatedFeedList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('feed.nodes.FeedNode')
