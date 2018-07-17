import graphene

class PaginatedGroupList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.nodes.GroupNode')

class PaginatedMembershipList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.nodes.GroupMembershipNode')

class PaginatedNodeList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List('core.nodes.Node')
