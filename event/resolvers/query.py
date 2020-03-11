from ariadne import ObjectType
from event.models import Event
from datetime import datetime
from django.utils import timezone

query = ObjectType("Query")

def get_end_of_yesterday():
    yesterday = timezone.now() - timezone.timedelta(days=1)

    return datetime(year=yesterday.year, month=yesterday.month,
                    day=yesterday.day, hour=23, minute=59, second=59)


@query.field("events")
def resolve_events(obj, info, filter=None, containerGuid=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    events = Event.objects.visible(info.context.user)

    if filter == 'previous':
        events = events.filter(start_date__lte=get_end_of_yesterday())
    else:
        events = events.filter(start_date__gt=get_end_of_yesterday())

    edges = events[offset:offset+limit]

    return {
        'total': events.count(),
        'edges': edges
    }
