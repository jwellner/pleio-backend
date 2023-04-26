from ariadne import ObjectType
from django.utils import timezone
from django.utils.timezone import timedelta

from core.lib import early_this_morning
from event.models import Event
from event.range.sync import complete_range

range_settings = ObjectType("EventRangeSettings")


@range_settings.field("isIgnored")
def resolve_is_ignored(obj, info):
    # pylint: disable=unused-argument
    event = obj['event']
    return event.range_ignore


@range_settings.field("repeatUntil")
def resolve_repeat_until(obj, info):
    # pylint: disable=unused-argument
    if obj.get('repeatUntil'):
        return timezone.datetime.fromisoformat(obj['repeatUntil'])
    return None


@range_settings.field("nextEvent")
def resolve_next_event(obj, info, timeAfter=None):
    # pylint: disable=unused-argument
    event = obj['event']
    if not timeAfter:
        timeAfter = event.start_date

    # Make sure events exist until this special date.
    if not event.range_closed:
        complete_range(event, early_this_morning(timeAfter) + timedelta(days=1))

    return Event.objects.get_range_after(event).filter(start_date__gt=timeAfter).first()
