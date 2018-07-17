import graphene
from graphene import relay
from .nodes import PaginatedList, Node, ViewerNode, GroupNode
from .models import Group

class Query(object):
    node = graphene.Field(Node)
    viewer = graphene.Field(ViewerNode)
    groups = graphene.Field(PaginatedList, offset=graphene.Int(required=True), limit=graphene.Int(required=True))

    def resolve_groups(self, info, offset=0, limit=20):
        return PaginatedList(
            totalCount=Group.objects.count(),
            edges=Group.objects.all()[offset:(offset+limit)]
        )

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user

        return ViewerNode(
            is_authenticated=user.is_authenticated,
            user=(user if user.is_authenticated else None)
        )
