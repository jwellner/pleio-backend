from django.utils import timezone
from django_elasticsearch_dsl.registries import registry

from event.models import Event


class RangeIndexProcessor:

    def __init__(self, number_of_events_ahead=None):
        self.now = timezone.now()
        self.number_of_events_ahead = number_of_events_ahead or 1

    def process(self):
        for range_master in Event.objects.filter_range_events(include_closed=True):
            self._process_range_master(range_master)

    def _process_range_master(self, range_master):
        valid_events = Event.objects.get_full_range(range_master).filter(end_date__gt=self.now).order_by('end_date')[:self.number_of_events_ahead]
        last_event = Event.objects.get_range_stopper(range_master)
        not_due_events = {'id__in': [*[e.id for e in valid_events], last_event.id]}

        due_events = Event.objects.get_full_range(range_master)
        due_events = due_events.filter(index_item=True)
        due_events = due_events.exclude(**not_due_events)

        for event in due_events:
            self._remove_from_index(event)

        for event in valid_events:
            self._add_to_index(event)

        if last_event not in valid_events and last_event.end_date < self.now:
            self._add_to_index(last_event)

    @staticmethod
    def _remove_from_index(event):
        if not event.index_item:
            return
        event.index_item = False
        event.save()
        registry.delete_related(event)
        registry.delete(event)

    @staticmethod
    def _add_to_index(event):
        if event.index_item:
            return
        event.index_item = True
        event.save()
