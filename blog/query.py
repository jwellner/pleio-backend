import graphene
from graphene_django import DjangoConnectionField

from .nodes import BlogNode
from .models import Blog

class Query(object):
    blogs = DjangoConnectionField(BlogNode)

    def resolve_blogs(self, info, **kwargs):
        return Blog.objects.visible(info.context.user)
