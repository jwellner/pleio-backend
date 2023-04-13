from django.utils import timezone
from django.utils.text import slugify
from graphql import GraphQLError
from core.constances import INVALID_NAME
from core.lib import get_base_url, early_this_morning


def get_url(obj):
    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return get_base_url() + '{}/events/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()


def validate_name(name):
    if not name or not len(name.strip()) > 2:
        raise GraphQLError(INVALID_NAME)
    return name.strip()


def complement_expected_range(events, offset, limit):
    least_starttime = None
    for start_date in events.values_list('start_date', flat=True)[:offset + limit]:
        if not start_date:
            continue
        if not least_starttime or start_date > least_starttime:
            least_starttime = early_this_morning(start_date + timezone.timedelta(days=1))

    if not least_starttime:
        least_starttime = early_this_morning(timezone.now() + timezone.timedelta(days=1))

    from event.range.sync import complete_range
    from event.models import Event
    for event in Event.objects.filter_range_events():
        complete_range(event, until=least_starttime, cycle=limit)


def mark_events_for_indexing(number_of_events_ahead=None):
    from event.range.index import RangeIndexProcessor
    processor = RangeIndexProcessor(number_of_events_ahead)
    processor.process()
