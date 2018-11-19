import graphene
from graphene_django.types import DjangoObjectType
from core.entities import Entity
from .models import Wiki as WikiModel


class Wiki(DjangoObjectType):
    class Meta:
        model = WikiModel
        interfaces = (Entity, )

    can_write = graphene.Boolean(required=True)

    def resolve_id(self, info):
        return '{}.{}:{}'.format(
            self._meta.app_label,
            self._meta.object_name,
            self.id
            ).lower()

    def resolve_can_write(self, info):
        return self.can_write(info.context.user)
