from unittest import mock

from django.utils import timezone
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from file.models import ScanIncident
from file.tasks import schedule_scan_finished
from user.factories import UserFactory


class TestTaskScheduleScanFinishedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = UserFactory(is_superadmin=True)

        mixer.blend(ScanIncident,
                    file_created=timezone.now(),
                    is_virus=True)
        mixer.blend(ScanIncident,
                    file_created=timezone.now())
        mixer.blend(ScanIncident,
                    file_created=timezone.now())
        mixer.blend(ScanIncident,
                    file_created=timezone.now() - timezone.timedelta(days=2))

    @mock.patch("file.tasks.schedule_file_scan_found_mail")
    def test_schedule_scan_finished(self, schedule_file_scan_found_mail):
        schedule_scan_finished(self.tenant.schema_name)

        self.assertTrue(schedule_file_scan_found_mail.called)
        self.assertEqual(schedule_file_scan_found_mail.call_args.kwargs, {
            'error_count': 2,
            'virus_count': 1,
            'admin': self.admin
        })
