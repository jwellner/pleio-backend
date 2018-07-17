import graphene
from core.nodes import PaginatedNodeList
from .nodes import BlogNode
from .models import Blog

class Query(object):
    blogs = graphene.Field(PaginatedNodeList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_blogs(self, info, offset=0, limit=20):
        return PaginatedNodeList(
            totalCount=Blog.objects.visible(info.context.user).count(),
            edges=Blog.objects.visible(info.context.user)[offset:(offset+limit)]
        )
