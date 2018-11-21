import graphene
from graphene_django.types import DjangoObjectType
from graphene import relay
from core.entities import Entity, User

class Notification(graphene.ObjectType):
    class Meta:
        interfaces = (Entity, )

    id = graphene.Int()
    action = graphene.String()
    performer = graphene.Field(User)
    entity = graphene.Field(Entity)
    container = graphene.Field(Entity)
    timeCreated = graphene.String()
    isUnread = graphene.Boolean()
