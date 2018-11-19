import graphene


class DiscussionList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('discussion.entities.Discussion')
