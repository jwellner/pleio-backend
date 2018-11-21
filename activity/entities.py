import graphene
from core.entities import Entity
from .enums import ACTIVITY_TYPES

ActivityType = graphene.Enum.from_enum(ACTIVITY_TYPES)

class Activity(graphene.ObjectType):
    class Meta:
        interfaces = (Entity, )

    guid = graphene.ID()
    type = ActivityType()
