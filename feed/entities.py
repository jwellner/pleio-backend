from graphene_django.types import DjangoObjectType
import graphene
from graphene import relay
from core.lib import get_type, get_id
from core.entities import Entity
from .models import Feed as FeedModel


class Feed(DjangoObjectType):
    class Meta:
        model = FeedModel
        interfaces = (Entity, )
        only_fields = ['id']

    node = graphene.Field(Entity)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

    def resolve_node(self, info):
        return self.node
