import graphene
from .lists import NewsList
from .models import News as NewsModel


class Query(object):
    """
    Does not exist in old graphQL schema

    news = graphene.Field(
        NewsList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_news(self, info, offset=0, limit=20):
        return NewsList(
            totalCount=NewsModel.objects.visible(info.context.user).count(),
            edges=NewsModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
    """
