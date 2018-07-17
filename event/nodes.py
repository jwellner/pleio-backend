from graphene_django.types import DjangoObjectType
from graphene import relay
from core.nodes import Node
from .models import Event

class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        interfaces = (Node, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()
