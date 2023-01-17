from django.utils import timezone

from core.lib import str_to_datetime
from core.tests.helpers import PleioTenantTestCase


class TestLibStrToDatetimeTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.reference_datetime = timezone.now()
        self.local_datetime = self.reference_datetime.astimezone(timezone.get_current_timezone())
        self.unaware_datetime = timezone.make_naive(self.local_datetime)

    def test_str_to_datetime(self):
        self.assertEqual(str_to_datetime(self.local_datetime.isoformat()), self.local_datetime)
        self.assertEqual(str_to_datetime(self.unaware_datetime.isoformat()), self.local_datetime)
        self.assertEqual(str_to_datetime(None), None)