from unittest import mock

from django.utils import timezone

from blog.factories import BlogFactory
from core.factories import AttachmentFactory
from core.models import Attachment
from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory
from file.models import FileFolder
from file.tasks import ScheduleScan, schedule_scan
from user.factories import UserFactory


class TestTaskScheduleScanTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.content = self.build_contentfile(self.relative_path(__file__, ['assets', 'navy.jpg']))

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

        self.blog = BlogFactory(owner=self.owner)
        self.attachments = [
            AttachmentFactory(owner=self.owner,
                              attached=self.blog,
                              upload=self.content,
                              last_scan=timezone.now() - timezone.timedelta(hours=1)).id,
            AttachmentFactory(owner=self.owner,
                              attached=self.blog,
                              upload=self.content,
                              last_scan=timezone.now() - timezone.timedelta(hours=10)).id,
            AttachmentFactory(owner=self.owner,
                              attached=self.blog,
                              upload=self.content,
                              last_scan=timezone.now() - timezone.timedelta(hours=2)).id,
        ]

    def tearDown(self):
        for a in Attachment.objects.all():
            a.delete()
        for f in FileFolder.objects.all():
            f.delete()
        self.blog.delete()
        self.owner.delete()
        super().tearDown()

    @mock.patch("file.models.FileFolderQuerySet.count")
    def test_file_count(self, mocked_count):
        self.override_setting(SCAN_CYCLE_DAYS="10")

        mocked_count.return_value = 100
        self.assertEqual(ScheduleScan().file_limit(), 10)

        mocked_count.return_value = 200
        self.assertEqual(ScheduleScan().file_limit(), 20)

    @mock.patch("core.models.attachment.AttachmentQuerySet.count")
    def test_attachment_count(self, mocked_count):
        self.override_setting(SCAN_CYCLE_DAYS="10")

        mocked_count.return_value = 100
        self.assertEqual(ScheduleScan().attachment_limit(), 10)

        mocked_count.return_value = 1000
        self.assertEqual(ScheduleScan().attachment_limit(), 100)

    @mock.patch("file.tasks.ScheduleScan.file_limit")
    def test_collect_files(self, file_limit):
        file_limit.return_value = 1
        result = ScheduleScan().collect_files()

        # second should be the middle of the scanned-before files.
        self.assertEqual([*result], [self.files[1]])

    @mock.patch("file.tasks.ScheduleScan.attachment_limit")
    def test_collect_attachments(self, file_limit):
        file_limit.return_value = 1
        result = ScheduleScan().collect_attachments()

        # second should be the middle of the scanned-before files.
        self.assertEqual([*result], [self.attachments[1]])

    @mock.patch("file.tasks.scan_file")
    @mock.patch("core.tasks.scan_attachment")
    @mock.patch("file.tasks.ScheduleScan.collect_files")
    @mock.patch("file.tasks.ScheduleScan.collect_attachments")
    def test_generate_tasks(self,
                            mocked_collect_attachments, mocked_collect_files,
                            mocked_scan_attachment, mocked_scan_file):
        mocked_collect_attachments.return_value = [self.attachments[0]]
        mocked_collect_files.return_value = [self.files[0]]
        mocked_scan_attachment.si.return_value = "SCAN_ATTACHMENT_SIGNATURE"
        mocked_scan_file.si.return_value = "SCAN_FILE_SIGNATURE"

        self.assertEqual([*ScheduleScan().generate_tasks(self.tenant.schema_name)], [
            "SCAN_FILE_SIGNATURE", "SCAN_ATTACHMENT_SIGNATURE"
        ])
        self.assertEqual(mocked_scan_file.si.call_args.args,
                         (self.tenant.schema_name, str(self.files[0])))
        self.assertEqual(mocked_scan_attachment.si.call_args.args,
                         (self.tenant.schema_name, str(self.attachments[0])))

    @mock.patch("file.tasks.chord")
    @mock.patch("file.tasks.ScheduleScan.generate_tasks")
    @mock.patch("file.tasks.schedule_scan_finished")
    def test_apply_async(self,
                         mocked_scan_finished,
                         mocked_generate_tasks,
                         mocked_chord):
        mocked_generate_tasks.return_value = ["SCAN_TASK_SIGNATURE"]
        mocked_scan_finished.si.return_value = "SCAN_COMPLETE_SIGNATURE"
        chord_task = mock.MagicMock()
        mocked_chord.return_value = chord_task

        ScheduleScan().run(self.tenant.schema_name)

        self.assertEqual(mocked_generate_tasks.call_args.args,
                         (self.tenant.schema_name,))
        self.assertEqual(mocked_chord.call_args.args, (["SCAN_TASK_SIGNATURE"], "SCAN_COMPLETE_SIGNATURE"))
        self.assertTrue(chord_task.apply_async.called)

    @mock.patch('file.tasks.ScheduleScan.run')
    def test_schedule_scan(self, mocked_run):
        schedule_scan(self.tenant.schema_name)

        self.assertTrue(mocked_run.called)
        self.assertEqual(mocked_run.call_args.args, (self.tenant.schema_name,))
