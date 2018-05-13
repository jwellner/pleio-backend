import graphene
from graphene_django.types import DjangoObjectType
from backend.core.models import User, Group

class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ['id', 'name', 'email']

class GroupType(DjangoObjectType):
    class Meta:
        model = Group

class ViewerType(graphene.ObjectType):
    is_authenticated = graphene.Boolean()
    user = graphene.Field(UserType)