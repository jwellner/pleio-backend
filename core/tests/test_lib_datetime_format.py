from django.utils import timezone

from core.lib import datetime_format
from core.tests.helpers import PleioTenantTestCase


class TestLibDatetimeFormat(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.reference_time = timezone.datetime.fromtimestamp(1617181920)
        self.local_time = self.reference_time.astimezone(timezone.get_current_timezone())
        self.utc_time = self.reference_time.astimezone(timezone.utc)

    def test_format_time(self):
        self.assertEqual(datetime_format(self.local_time), "2021-03-31 11:12")

    def test_format_time_between_timezones(self):
        self.assertEqual(datetime_format(self.utc_time),
                         datetime_format(self.local_time))

        self.assertNotEqual(self.utc_time.isoformat(),
                            self.local_time.isoformat())

    def test_format_non_time(self):
        self.assertEqual(datetime_format("Foo"), "")

    def test_format_datetime_with_seconds(self):
        result = datetime_format(self.reference_time, seconds=True)

        self.assertEqual(result, '2021-03-31 11:12:00')