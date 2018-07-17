from graphene_django.types import DjangoObjectType
from graphene import relay
from core.nodes import Node
from .models import Blog

class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        interfaces = (Node, )
