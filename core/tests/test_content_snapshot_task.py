from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import UserFactory


class TestActivitySnapshotTaskTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.other_user = UserFactory()

    def tearDown(self):
        for file in FileFolder.objects.all():
            file.delete()

        self.user.delete()
        self.other_user.delete()

        super().tearDown()

    @mock.patch("core.mail_builders.content_export_ready.schedule_content_export_ready_mail")
    @mock.patch("core.utils.export.content.ContentSnapshot.collect_content")
    def test_execute_task(self, collect_content, send_mail):
        collect_content.return_value = b"not a zip file"
        from core.tasks.exports import export_my_content
        export_my_content(self.tenant.schema_name, self.user.guid)

        content_snapshots = FileFolder.objects.content_snapshots(user=self.user)
        snapshot_file = content_snapshots.first()

        self.assertTrue(collect_content.called)
        self.assertTrue(send_mail.called)
        self.assertEqual(1, content_snapshots.count())

        self.assertEqual(snapshot_file.owner, self.user)
        self.assertFalse(snapshot_file.can_read(self.other_user))
        self.assertFalse(snapshot_file.can_write(self.other_user))

        from core.utils.export.content import ContentSnapshot
        self.assertEqual(snapshot_file.tags, [ContentSnapshot.EXCLUDE_TAG])
