import graphene
from .lists import PaginatedNewsList
from .nodes import NewsNode
from .models import News

class Query(object):
    news = graphene.Field(PaginatedNewsList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_news(self, info, offset=0, limit=20):
        return PaginatedNewsList(
            totalCount=News.objects.visible(info.context.user).count(),
            edges=News.objects.visible(info.context.user)[offset:(offset+limit)]
        )
