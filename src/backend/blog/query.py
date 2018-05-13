import graphene

from .types import BlogType
from .models import Blog

class Query(object):
    blogs = graphene.List(BlogType)

    def resolve_blogs(self, info, **kwargs):
        return Blog.objects.visible(info.context.user)
