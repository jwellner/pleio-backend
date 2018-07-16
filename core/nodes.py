import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from core.models import User, Group

class UserNode(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name', 'picture']
        interfaces = (relay.Node, )

    def resolve_id(self, info):
        return 'user:{}'.format(self.id)

class GroupNode(DjangoObjectType):
    class Meta:
        model = Group
        filter_fields = {
            'name': ['icontains']
        }
        interfaces = (relay.Node, )

    def resolve_id(self, info):
        return 'group:{}'.format(self.id)

class ViewerNode(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node, )

    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserNode)