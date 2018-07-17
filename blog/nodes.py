from graphene_django.types import DjangoObjectType
from graphene import relay
from core.nodes import Node
from .models import Blog

class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        interfaces = (Node, )

    def resolve_id(self, info):
        return '{}.{}:{}'.format(self._meta.app_label, self._meta.object_name, self.id).lower()
