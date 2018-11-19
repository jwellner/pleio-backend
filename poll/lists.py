import graphene

class PollList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('poll.entities.Poll')
