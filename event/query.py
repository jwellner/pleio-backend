import graphene
from .lists import PaginatedEventList
from .nodes import EventNode
from .models import Event

class Query(object):
    events = graphene.Field(PaginatedEventList, offset=graphene.Int(), limit=graphene.Int())

    def resolve_events(self, info, offset=0, limit=20):
        return PaginatedEventList(
            totalCount=Event.objects.visible(info.context.user).count(),
            edges=Event.objects.visible(info.context.user)[offset:(offset+limit)]
        )
