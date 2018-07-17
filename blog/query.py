import graphene
from core.nodes import PaginatedList
from .nodes import BlogNode
from .models import Blog

class Query(object):
    blogs = graphene.Field(PaginatedList, offset=graphene.Int(required=True), limit=graphene.Int(required=True))

    def resolve_blogs(self, info, offset=0, limit=20):
        return PaginatedList(
            totalCount=Blog.objects.count(),
            edges=Blog.objects.visible(info.context.user)[offset:(offset+limit)]
        )
