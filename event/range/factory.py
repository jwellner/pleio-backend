from django.utils import timezone

from event.models import Event
from event.range.calculator import RangeCalculator


class EventRangeFactory:
    class EventRangeCompleteError(Exception):
        pass

    def __init__(self, event: Event):
        self.event = event

    @property
    def last_event(self):
        return Event.objects.get_range_stopper(self.event) or self.event

    def get_last_referable(self):
        return Event.objects.get_range_last_referable(self.event) or self.last_event

    @property
    def repeat_until(self):
        return self.event.range_settings.get('repeatUntil')

    @property
    def instance_limit(self):
        return self.event.range_settings.get('instanceLimit')

    def assert_due_date_valid(self, next_starttime):
        if not self.repeat_until:
            return

        until = timezone.datetime.fromisoformat(self.repeat_until)
        if next_starttime <= until:
            return

        raise self.EventRangeCompleteError()

    def assert_instance_count_valid(self):
        if not self.instance_limit:
            return

        range_items = Event.objects.get_full_range(self.event)
        if self.instance_limit > range_items.count():
            return

        raise self.EventRangeCompleteError()

    def create_next_event(self):
        last = self.last_event
        last_referable = self.get_last_referable()
        next_starttime = RangeCalculator(last).next()

        try:
            self.assert_due_date_valid(next_starttime)
            self.assert_instance_count_valid()

            next_event: Event = Event.objects.create(owner=self.event.owner,
                                                     range_master=last.range_master or self.event,
                                                     range_settings=last_referable.range_settings,
                                                     range_starttime=next_starttime,
                                                     index_item=False)
            Event.objects.filter(id=next_event.id).update_range(last_referable)
            next_event.refresh_from_db()
            return next_event
        except self.EventRangeCompleteError:
            pass


def complete_range(reference, until, cycle=1):
    section = Event.objects.get_full_range(reference).filter(start_date__gte=until)
    if section.count() >= cycle:
        # Range is complete
        return

    factory = EventRangeFactory(Event.objects.get_range_stopper(reference))
    next_event = factory.create_next_event()

    if not next_event:
        # Range is due
        Event.objects.get_full_range(reference).update(range_closed=True)
    else:
        # Try again.
        complete_range(reference, until, cycle)
