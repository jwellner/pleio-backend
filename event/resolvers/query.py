from ariadne import ObjectType
from event.models import Event


query = ObjectType("Query")

@query.field("events")
def resolve_events(obj, info, filter=None, containerGuid=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    events = []

    events = Event.objects.all()[offset:offset+limit]

    return {
        'total': events.count(),
        'canWrite': False,
        'edges': events
    }
