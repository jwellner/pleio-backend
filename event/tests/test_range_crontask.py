from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from event.tasks import process_range_events


class TestRangeCrontaskTestCase(PleioTenantTestCase):

    @mock.patch("event.tasks.complement_expected_range")
    @mock.patch("event.tasks.mark_events_for_indexing")
    def test_crontask(self, mark_events_for_indexing, complement_expected_range):
        process_range_events(self.tenant.schema_name)

        self.assertTrue(complement_expected_range.called)
        self.assertEqual(complement_expected_range.call_args.args[0].count(), 0)
        self.assertEqual(complement_expected_range.call_args.kwargs, {'offset': 0, 'limit': 2})
        self.assertTrue(mark_events_for_indexing.called)
        self.assertEqual(mark_events_for_indexing.call_args.kwargs, {'number_of_events_ahead': 2})
