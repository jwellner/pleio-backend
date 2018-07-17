import graphene
from graphene import relay
from .nodes import Node, ViewerNode, GroupNode, GroupMembershipNode
from .lists import PaginatedGroupList
from .models import Group

class Query(object):
    node = graphene.Field(Node)
    viewer = graphene.Field(ViewerNode)
    groups = graphene.Field(PaginatedGroupList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_groups(self, info, offset=0, limit=20):
        return PaginatedGroupList(
            totalCount=Group.objects.count(),
            edges=Group.objects.all()[offset:(offset+limit)]
        )

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user

        return ViewerNode(
            is_authenticated=user.is_authenticated,
            user=(user if user.is_authenticated else None)
        )
