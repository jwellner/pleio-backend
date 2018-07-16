from graphene_django.types import DjangoObjectType
from graphene import relay
from .models import Blog

class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        interfaces = (relay.Node, )

    def resolve_id(self, info):
        return 'blog:{}'.format(self.id)
