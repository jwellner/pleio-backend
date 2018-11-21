import graphene
from .lists import EventList
from .models import Event as EventModel
from .enums import EVENT_FILTER

EventFilter = graphene.Enum.from_enum(EVENT_FILTER)

class Query(object):
    events = graphene.Field(
        EventList,
        filter=EventFilter(),
        containerGuid=graphene.Int(),
        offset=graphene.Int(),
        limit=graphene.Int()
    )

    def resolve_events(self, info, offset=0, limit=20):
        return EventList(
            total=EventModel.objects.visible(info.context.user).count(),
            can_write=EventModel.can_write,
            edges=EventModel.objects.visible(
                info.context.user
                )[offset:(offset+limit)]
        )
