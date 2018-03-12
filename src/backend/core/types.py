from graphene_django.types import DjangoObjectType
from backend.core.models import Group

class GroupType(DjangoObjectType):
    class Meta:
        model = Group
