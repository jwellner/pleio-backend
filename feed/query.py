import graphene
from .lists import PaginatedFeedList
from .models import Feed

class Query(object):
    feed = graphene.Field(PaginatedFeedList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_feed(self, info, offset=0, limit=20):
        return PaginatedFeedList(
            totalCount=Feed.objects.visible(info.context.user).count(),
            edges=Feed.objects.visible(info.context.user).order_by('-id')[offset:(offset+limit)]
        )
