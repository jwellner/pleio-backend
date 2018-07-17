import graphene
from graphene_django.types import DjangoObjectType
from .models import User, Group, GroupMembership
from .lists import PaginatedMembershipList

class Node(graphene.Interface):
    id = graphene.ID()

class UserNode(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name', 'picture']
        interfaces = (Node, )

    def resolve_id(self, info):
        return 'user:{}'.format(self.id)

class GroupNode(DjangoObjectType):
    class Meta:
        model = Group
        interfaces = (Node, )

    membership = graphene.Field(PaginatedMembershipList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_id(self, info):
        return 'group:{}'.format(self.id)

    def resolve_membership(self, info, offset=0, limit=20):
        return PaginatedMembershipList(
            totalCount=self.membership.count(),
            edges=self.membership.all()[offset:(offset+limit)]
        )

class GroupMembershipNode(DjangoObjectType):
    class Meta:
        model = GroupMembership
        interfaces = (Node, )

    def resolve_id(self, info):
        return 'group_membership:{}'.format(self.id)

class ViewerNode(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserNode)
