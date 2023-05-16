from unittest import mock

from django.utils import timezone
from django.utils.timezone import timedelta

from core.lib import early_this_morning
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.lib import complement_expected_range
from event.models import Event
from event.range.calculator import DayOfTheWeekRange, DailyRange
from event.range.sync import complete_range
from user.factories import UserFactory


def create_timestamp(timestamp):
    return timezone.datetime.fromisoformat(timestamp)


class TestRangeFactoryTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.STARTTIME = create_timestamp("2020-10-10T10:00:00.000000+01:00")
        self.TWENTYDAYSAHEAD = create_timestamp("2020-10-30T10:00:00.000000+01:00")
        self.FUTURETIME = create_timestamp("2021-02-15T10:00:00.000000+01:00")
        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_starttime=self.STARTTIME,
                                  start_date=self.STARTTIME,
                                  end_date=self.STARTTIME + timedelta(hours=1),
                                  range_settings={
                                      "type": DayOfTheWeekRange.key,
                                      "interval": 1,
                                  })

    def test_create_next_event(self):
        complete_range(self.event, self.FUTURETIME)
        self.event.refresh_from_db()

        items = Event.objects.get_full_range(self.event).order_by('range_starttime')
        self.assertEqual(len(items), 20)

    def test_create_event_until_date(self):
        self.event.range_settings['repeatUntil'] = self.TWENTYDAYSAHEAD.isoformat()
        self.event.save()

        complete_range(self.event, self.FUTURETIME)
        self.event.refresh_from_db()

        items = Event.objects.get_full_range(self.event).order_by('range_starttime')
        self.assertEqual(len(items), 3)

    def test_create_event_with_cycles(self):
        complete_range(self.event, self.event.range_starttime)
        self.assertEqual(Event.objects.get_full_range(self.event).count(), 1)

        complete_range(self.event, self.event.range_starttime, 5)
        self.assertEqual(Event.objects.get_full_range(self.event).count(), 5)

    def test_create_event_until_instances_count(self):
        self.event.range_settings['instanceLimit'] = 5
        self.event.save()

        complete_range(self.event, self.FUTURETIME)
        self.event.refresh_from_db()

        items = Event.objects.get_full_range(self.event).order_by('range_starttime')
        self.assertEqual(len(items), 5)

    def test_create_next_event_when_all_items_are_ignored(self):
        Event.objects.get_full_range(self.event).update(range_ignore=True)
        self.event.refresh_from_db()

        complete_range(self.event, self.FUTURETIME)
        items = Event.objects.get_full_range(self.event).order_by('range_starttime')
        self.assertEqual(len(items), 20)


class TestComplementExpectedRange(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.reference_time = timezone.now()
        self.owner = UserFactory()
        self.event1 = EventFactory(owner=self.owner,
                                   title="Recurring event",
                                   start_date=self.reference_time - timedelta(days=10),
                                   range_starttime=self.reference_time,
                                   range_settings={})
        self.event2 = EventFactory(owner=self.owner,
                                   title="Single event",
                                   start_date=self.reference_time,
                                   end_date=self.reference_time + timedelta(hours=1))

        self.get_range_events = mock.patch("event.models.EventQuerySet.filter_range_events").start()
        self.get_range_events.return_value = Event.objects.filter(id=self.event1.id)

        self.complete_range = mock.patch("event.range.sync.complete_range").start()

    def tearDown(self):
        super().tearDown()

    def test_complement_expected_range(self):
        expected_time = timezone.now() - timedelta(days=20)
        timezone_now = mock.patch("django.utils.timezone.now").start()
        timezone_now.return_value = expected_time

        complement_expected_range(Event.objects.filter(id=self.event2.id), 1, 1)

        self.assertEqual(self.complete_range.call_args.args, (self.event1,))
        self.assertEqual(self.complete_range.call_args.kwargs, {'until': early_this_morning(self.event2.start_date) + timedelta(days=1),
                                                                'cycle': 1})

    def test_complement_expected_range_when_empty(self):
        expected_time = timezone.now() - timedelta(days=20)
        timezone_now = mock.patch("django.utils.timezone.now").start()
        timezone_now.return_value = expected_time

        complement_expected_range(Event.objects.none(), 1, 1)
        self.assertEqual(self.complete_range.call_args.args, (self.event1,))
        self.assertEqual(self.complete_range.call_args.kwargs, {'until': early_this_morning(expected_time) + timedelta(days=1),
                                                                'cycle': 1})


class TestCloseFiniteRangeTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.reference_time = timezone.now()
        self.owner = UserFactory()

        self.event: Event = EventFactory(owner=self.owner,
                                         start_date=self.reference_time,
                                         end_date=self.reference_time + timedelta(hours=3),
                                         range_starttime=self.reference_time,
                                         range_settings={
                                             "type": DailyRange.key,
                                             "interval": 1,
                                         })

    def test_not_closing_the_range(self):
        complete_range(self.event, self.reference_time, 5)
        self.event.refresh_from_db()
        self.assertFalse(self.event.range_closed)

    def test_closing_the_range(self):
        self.event.range_settings['instanceLimit'] = 4
        self.event.save()

        complete_range(self.event, self.reference_time, 5)
        self.event.refresh_from_db()
        self.assertTrue(self.event.range_closed)
