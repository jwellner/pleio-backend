import graphene

class PaginatedPollList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('poll.nodes.PollNode')
