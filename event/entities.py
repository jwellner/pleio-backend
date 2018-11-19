from graphene_django.types import DjangoObjectType
from graphene import relay
from core.entities import Entity
from .models import Event as EventModel


class Event(DjangoObjectType):
    class Meta:
        model = EventModel
        interfaces = (Entity, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()
