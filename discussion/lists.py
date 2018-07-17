import graphene

class PaginatedDiscussionList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('discussion.nodes.DiscussionNode')