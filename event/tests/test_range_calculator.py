from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.range.calculator import RangeCalculator, DailyRange, DayOfTheWeekRange, DayOfTheMonthRange, WeekdaydOfTheMonthRange
from user.factories import UserFactory


def create_timestamp(timestamp):
    return timezone.datetime.fromisoformat(timestamp)


class TestRangeCalculatorDailyTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_starttime=create_timestamp("2020-10-10T10:00:00.000000+01:00"),
                                  range_settings={
                                      "type": DailyRange.key,
                                      "interval": 1,
                                  })

    def test_every_day(self):
        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, self.event.range_starttime.day + 1)

    def test_every_3rd_day(self):
        self.event.range_settings['interval'] = 3

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, self.event.range_starttime.day + 3)


class TestRangeCalculatorDayOfTheWeekTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_starttime=create_timestamp("2020-10-10T10:00:00.000000+01:00"),
                                  range_settings={
                                      "type": DayOfTheWeekRange.key,
                                      "interval": 1,
                                  })

    def test_every_week_same_day(self):
        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, self.event.range_starttime.day + 7)

    def test_every_other_week_same_day(self):
        self.event.range_settings['interval'] = 2

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, self.event.range_starttime.day + 14)


class TestRangeCalculatorDayOfTheMonthTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_starttime=create_timestamp("2020-01-10T10:00:00.000000+01:00"),
                                  range_settings={
                                      "type": DayOfTheMonthRange.key,
                                      "interval": 1,
                                  })

    def test_every_month_same_dom(self):
        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 1)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, self.event.range_starttime.day)

    def test_every_3rd_month_same_day(self):
        self.event.range_settings['interval'] = 3

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 3)
        self.assertEqual(next_time.day, self.event.range_starttime.day)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)

    def test_every_month_last_month_day(self):
        self.event.range_starttime = create_timestamp("2020-01-31T10:00:00.000000+01:00")

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 1)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        # Shorter month, Leap year.
        self.assertEqual(next_time.day, 29)


class TestRangeCalculatorWeedaykOfTheMonthTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_starttime=create_timestamp("2022-10-01T10:00:00.000000+01:00"),
                                  range_settings={
                                      "type": WeekdaydOfTheMonthRange.key,
                                      "interval": 1,
                                  })

    def test_every_month_same_dow(self):
        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 1)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, 5)

    def test_every_month_same_dow_backwards(self):
        self.event.range_starttime = create_timestamp("2023-04-03T10:00:00.000000+01:00")

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 1)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, 1)

    def test_every_4th_month_same_dow(self):
        self.event.range_starttime = create_timestamp("2023-04-03T10:00:00.000000+01:00")
        self.event.range_settings['interval'] = 4

        range = RangeCalculator(self.event)
        next_time = range.next()

        self.assertEqual(next_time.year, self.event.range_starttime.year)
        self.assertEqual(next_time.month, self.event.range_starttime.month + 4)
        self.assertEqual(next_time.hour, self.event.range_starttime.hour)
        self.assertEqual(next_time.minute, self.event.range_starttime.minute)
        self.assertEqual(next_time.second, self.event.range_starttime.second)
        self.assertEqual(next_time.day, 7)
