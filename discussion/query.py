import graphene
from .lists import DiscussionList
from .models import Discussion as DiscussionModel


class Query(object):
    discussions = graphene.Field(
        DiscussionList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_discussions(self, info, offset=0, limit=20):
        return DiscussionList(
            totalCount=DiscussionModel.objects.visible(info.context.user).count(),
            edges=DiscussionModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
