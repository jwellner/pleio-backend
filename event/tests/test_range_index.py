from unittest import mock

from django.utils import timezone
from django.utils.timezone import timedelta

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.range.index import RangeIndexProcessor
from event.range.sync import complete_range
from user.factories import UserFactory


class TestIndexActiveEventsOnlyTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.reference_date = timezone.now() - timedelta(weeks=3)
        self.owner = UserFactory()
        self.range_master = EventFactory(owner=self.owner,
                                         start_date=self.reference_date,
                                         range_starttime=self.reference_date,
                                         range_settings={
                                             'type': 'daily',
                                             'interval': 7,
                                         })
        self.due_master = EventFactory(owner=self.owner,
                                       start_date=self.reference_date,
                                       range_starttime=self.reference_date,
                                       range_closed=True,
                                       range_settings={
                                           'type': 'daily',
                                           'interval': 7,
                                           'instanceLimit': 1
                                       })
        complete_range(self.range_master, self.reference_date + timedelta(weeks=6, days=-1))

    # should mark currently busy and first future event positive for indexing
    # should mark last event of closed ranges positive for indexing

    @mock.patch("event.range.index.RangeIndexProcessor._process_range_master")
    def test_process_all_range_masters(self, process_range_master):
        processor = RangeIndexProcessor()
        processor.process()

        self.assertEqual(process_range_master.call_count, 2)
        self.assertEqual({c.args[0] for c in process_range_master.call_args_list}, {self.range_master, self.due_master})

    @mock.patch("event.range.index.RangeIndexProcessor._add_to_index")
    def test_add_events_to_index(self, add_to_index):
        # Should have called add to index total of 3 times for total of 2 ranges
        processor = RangeIndexProcessor()
        processor.process()

        added_titles = {call.args[0].title for call in add_to_index.call_args_list}
        self.assertEqual(added_titles, {self.range_master.title,
                                        self.range_master.title,
                                        self.due_master.title})

        added_guids = {call.args[0].guid for call in add_to_index.call_args_list}
        self.assertNotIn(self.range_master.guid, added_guids)
        self.assertIn(self.due_master.guid, added_guids)

    @mock.patch("event.range.index.RangeIndexProcessor._remove_from_index")
    def test_remove_events_from_index(self, remove_from_index):
        # mark all for indexing, and notice that only a few are removed from the index.
        processor = RangeIndexProcessor()
        processor.process()

        removed_titles = {call.args[0].title for call in remove_from_index.call_args_list}
        self.assertIn(self.range_master.title, removed_titles)
        self.assertNotIn(self.due_master, removed_titles)

        removed_guids = {call.args[0].guid for call in remove_from_index.call_args_list}
        self.assertIn(self.range_master.guid, removed_guids)
        self.assertNotIn(self.due_master, removed_guids)

    @mock.patch("event.range.index.registry.delete")
    @mock.patch("event.range.index.registry.delete_related")
    def test_remove_one_event_from_index_if_not_in_index(self, delete_related, delete):
        # Given.
        self.range_master.index_item = False
        self.range_master.save()

        # When.
        RangeIndexProcessor._remove_from_index(self.range_master)
        self.range_master.refresh_from_db()

        # Then
        self.assertEqual(self.range_master.index_item, False)
        self.assertFalse(delete.called)
        self.assertFalse(delete_related.called)

    @mock.patch("event.range.index.registry.delete")
    @mock.patch("event.range.index.registry.delete_related")
    def test_remove_one_event_from_index_if_in_index(self, delete_related, delete):
        # Given.
        self.range_master.index_item = True
        self.range_master.save()

        # When.
        RangeIndexProcessor._remove_from_index(self.range_master)
        self.range_master.refresh_from_db()

        # Then
        self.assertEqual(self.range_master.index_item, False)
        self.assertTrue(delete.called)
        self.assertTrue(delete_related.called)

    def test_add_one_event_to_index_if_not_in_index(self):
        # Given.
        self.range_master.index_item = False
        self.range_master.save()

        # When.
        RangeIndexProcessor._add_to_index(self.range_master)
        self.range_master.refresh_from_db()

        # Then.
        self.assertEqual(self.range_master.index_item, True)

    def test_add_one_event_to_index_if_in_index(self):
        # Given.
        save_patch = mock.patch('event.models.Event.save')
        self.range_master.index_item = True
        self.range_master.save()

        # When.
        save = save_patch.start()
        RangeIndexProcessor._add_to_index(self.range_master)
        self.range_master.refresh_from_db()

        # Then.
        self.assertEqual(self.range_master.index_item, True)
        self.assertFalse(save.called)
