from unittest import mock

from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory
from file.models import FileFolder
from file.tasks import ScheduleScan, schedule_scan, scan_file
from user.factories import UserFactory


class TestTaskScheduleScanTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.content = self.build_contentfile(self.relative_path(__file__, ['assets', 'navy.jpg']))
        self.reference_time = timezone.now()

        self.files = [
            FileFactory(owner=self.owner,
                        upload=self.content,
                        last_scan=timezone.now() - timezone.timedelta(hours=1)).id,
            FileFactory(owner=self.owner,
                        upload=self.content,
                        last_scan=timezone.now() - timezone.timedelta(hours=10)).id,
            FileFactory(owner=self.owner,
                        upload=self.content,
                        last_scan=timezone.now() - timezone.timedelta(hours=2)).id,
        ]

    def tearDown(self):
        super().tearDown()

    @mock.patch("file.models.FileFolderQuerySet.count")
    def test_file_count(self, mocked_count):
        self.override_setting(SCAN_CYCLE_DAYS="10")

        mocked_count.return_value = 100
        self.assertEqual(ScheduleScan(self.tenant.schema_name, 0).file_limit(), 10)

        mocked_count.return_value = 200
        self.assertEqual(ScheduleScan(self.tenant.schema_name, 0).file_limit(), 20)

    @mock.patch("file.tasks.ScheduleScan.file_limit")
    def test_collect_files(self, file_limit):
        file_limit.return_value = 1
        result = ScheduleScan(self.tenant.schema_name, 0).collect_files()

        # second should be the middle of the scanned-before files.
        self.assertEqual([*result], [self.files[1]])

    @mock.patch("file.tasks.signature")
    @mock.patch("file.tasks.ScheduleScan.collect_files")
    @mock.patch("file.tasks.timezone.now")
    def test_generate_tasks(self, timezone_now, mocked_collect_files, signature):
        mocked_collect_files.return_value = [self.files[0]]
        signature.return_value = "SCAN_FILE_SIGNATURE"
        timezone_now.return_value = self.reference_time
        scheduler = ScheduleScan(self.tenant.schema_name, 0)

        tasks = [*scheduler.generate_tasks()]

        self.assertEqual(tasks, ["SCAN_FILE_SIGNATURE"])
        self.assertEqual(signature.call_args.kwargs, dict(args=(self.tenant.schema_name, str(self.files[0])),
                                                          eta=self.reference_time))

    @mock.patch("file.tasks.signature")
    @mock.patch("file.tasks.ScheduleScan.collect_files")
    @mock.patch("file.tasks.timezone.now")
    def test_generate_tasks_with_offset(self, timezone_now, mocked_collect_files, signature):
        mocked_collect_files.return_value = [self.files[0]]
        signature.return_value = "SCAN_FILE_SIGNATURE"
        timezone_now.return_value = self.reference_time
        scheduler = ScheduleScan(self.tenant.schema_name, 10)

        tasks = [*scheduler.generate_tasks()]
        self.assertEqual(tasks, ["SCAN_FILE_SIGNATURE"])
        self.assertEqual(signature.call_args.kwargs, dict(args=(self.tenant.schema_name, str(self.files[0])),
                                                          eta=self.reference_time+timezone.timedelta(seconds=10)))

    @mock.patch("file.tasks.chord")
    @mock.patch("file.tasks.ScheduleScan.generate_tasks")
    @mock.patch("file.tasks.schedule_scan_finished")
    def test_apply_async(self,
                         mocked_scan_finished,
                         mocked_generate_tasks,
                         mocked_chord):
        mocked_generate_tasks.return_value = ["SCAN_TASK_SIGNATURE"]
        mocked_scan_finished.si.return_value = "SCAN_COMPLETE_SIGNATURE"
        chord_return_value = mock.MagicMock()
        mocked_chord.return_value = chord_return_value

        scheduler = ScheduleScan(self.tenant.schema_name, 0)
        result = scheduler.run()

        self.assertEqual(1, result)
        self.assertEqual(mocked_chord.call_args.args, (["SCAN_TASK_SIGNATURE"], "SCAN_COMPLETE_SIGNATURE"))
        self.assertTrue(chord_return_value.apply_async.called)

    @mock.patch('file.tasks.ScheduleScan.run')
    def test_schedule_scan(self, mocked_run):
        schedule_scan(self.tenant.schema_name)

        self.assertTrue(mocked_run.called)
