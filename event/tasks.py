from celery import shared_task
from django_tenants.utils import schema_context

from event.lib import complement_expected_range, mark_events_for_indexing
from event.models import Event


@shared_task(ignore_result=True)
def process_range_events(schema_name):
    with schema_context(schema_name):
        # Add the two next events
        complement_expected_range(Event.objects.none(), offset=0, limit=2)
        # Add first two next events to index
        mark_events_for_indexing(number_of_events_ahead=2)
