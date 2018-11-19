import graphene
from .lists import BlogList
from .models import Blog


class Query(object):
    blogs = graphene.Field(
        BlogList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_blogs(self, info, offset=0, limit=20):
        return BlogList(
            totalCount=Blog.objects.visible(info.context.user).count(),
            edges=Blog.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
