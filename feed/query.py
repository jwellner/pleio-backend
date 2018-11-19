import graphene
from .lists import FeedList
from .models import Feed as FeedModel


class Query(object):
    feed = graphene.Field(
        FeedList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_feed(self, info, offset=0, limit=20):
        return FeedList(
            totalCount=FeedModel.objects.visible(info.context.user).count(),
            edges=FeedModel.objects.visible(
                info.context.user
                ).order_by('-id')[offset:(offset+limit)]
        )
