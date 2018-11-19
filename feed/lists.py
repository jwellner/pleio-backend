import graphene


class FeedList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('feed.entities.Feed')
