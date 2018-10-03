import graphene
from .lists import PaginatedDiscussionList
from .nodes import DiscussionNode
from .models import Discussion


class Query(object):
    discussions = graphene.Field(
        PaginatedDiscussionList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_discussions(self, info, offset=0, limit=20):
        return PaginatedDiscussionList(
            totalCount=Discussion.objects.visible(info.context.user).count(),
            edges=Discussion.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
