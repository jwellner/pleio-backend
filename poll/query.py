import graphene
from .lists import PollList
from .models import Poll as PollModel

class Query(object):
    """
    Does not exist in old graphQL schema

    polls = graphene.Field(
        PollList,
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    def resolve_polls(self, info, offset=0, limit=20):
        return PollList(
            totalCount=PollModel.objects.visible(info.context.user).count(),
            edges=PollModel.objects.visible(info.context.user)[offset:(offset+limit)]
        )
    """
