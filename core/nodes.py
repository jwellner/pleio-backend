import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from core.models import User, Group

class Node(graphene.Interface):
    id = graphene.ID()

class PaginatedNodeList(graphene.ObjectType):
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
    class Meta:
        model = Group
        filter_fields = {
            'name': ['icontains']
        }
        interfaces = (Node, )

    def resolve_id(self, info):
        return 'group:{}'.format(self.id)

class PaginatedGroupList(graphene.ObjectType):
    totalCount = graphene.Int(required=True)
    edges = graphene.List(GroupNode)

class ViewerNode(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserNode)