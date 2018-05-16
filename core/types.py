import graphene
from graphene_django.types import DjangoObjectType
from core.models import User, Group

class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name']

    def resolve_id(self, info):
        return 'user:{}'.format(self.id)

class GroupType(DjangoObjectType):
    class Meta:
        model = Group

    def resolve_id(self, info):
        return 'group:{}'.format(self.id)

class ViewerType(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserType)