import graphene
from .lists import EventList
from .models import Event as EventModel


class Query(object):
    events = graphene.Field(
        EventList,
        offset=graphene.Int(),
        limit=graphene.Int()
        )

    def resolve_events(self, info, offset=0, limit=20):
        return EventList(
            totalCount=EventModel.objects.visible(info.context.user).count(),
            edges=EventModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
