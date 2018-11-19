import graphene
from .lists import PaginatedPollList
from .nodes import PollNode
from .models import Poll

class Query(object):
    polls = graphene.Field(PaginatedPollList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_polls(self, info, offset=0, limit=20):
        return PaginatedPollList(
            totalCount=Poll.objects.visible(info.context.user).count(),
            edges=Poll.objects.visible(info.context.user)[offset:(offset+limit)]
        )
