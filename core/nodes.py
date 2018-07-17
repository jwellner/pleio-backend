import graphene
from graphene_django.types import DjangoObjectType
from core.models import User, Group, GroupMembership

class Node(graphene.Interface):
    id = graphene.ID()

class PaginatedList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List(Node)

class UserNode(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name', 'picture']
        interfaces = (Node, )

    def resolve_id(self, info):
        return 'user:{}'.format(self.id)

class GroupNode(DjangoObjectType):

    members = graphene.Field(PaginatedList, offset=graphene.Int(required=True), limit=graphene.Int(required=True))

    class Meta:
        model = Group
        filter_fields = {
            'name': ['icontains']
        }
        interfaces = (Node, )

    def resolve_id(self, info):
        return 'group:{}'.format(self.id)

    def resolve_members(self, info, offset=0, limit=20):
        return PaginatedList(
            totalCount=self.membership.count(),
            edges=self.membership.all()[offset:(offset+limit)]
        )

class GroupMembershipNode(DjangoObjectType):

    class Meta:
        model = GroupMembership
        interfaces = (Node,)

    def resolve_id(self, info):
        return 'group_membership:{}'.format(self.id)

class ViewerNode(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserNode)
