from django.utils.timezone import localtime, timedelta

from core.models import AvatarExport
from core.tasks.cronjobs import cleanup_exports
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import UserFactory


class TestAvatarExportCleanupTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.new_file = self.file_factory(self.relative_path(__file__, ['assets', 'avatar_export.zip']))
        self.new_export = AvatarExport.objects.create(
            initiator=self.owner,
            status='ready',
            file=self.new_file,
        )

        self.old_file = self.file_factory(self.relative_path(__file__, ['assets', 'avatar_export.zip']))
        self.old_export = AvatarExport.objects.create(
            initiator=self.owner,
            status='ready',
            file=self.old_file,
        )
        self.update_datetime(self.old_export, localtime() - timedelta(days=31))

        self.unfinished_export = AvatarExport.objects.create(
            initiator=self.owner,
            status='in_progres',
        )
        self.update_datetime(self.unfinished_export, localtime() - timedelta(days=31))

        self.recent_unfinished_export = AvatarExport.objects.create(
            initiator=self.owner,
            status='in_progres',
            updated_at=localtime() - timedelta(days=29)
        )
        self.update_datetime(self.recent_unfinished_export, localtime() - timedelta(days=29))

    def update_datetime(self, export, new_time):
        AvatarExport.objects.filter(id=export.id).update(updated_at=new_time)

    def test_remove_exports(self):
        cleanup_exports(self.tenant.schema_name)

        self.assertTrue(AvatarExport.objects.filter(id=self.new_export.guid).exists())
        self.assertFalse(AvatarExport.objects.filter(id=self.old_export.guid).exists())

        self.assertTrue(FileFolder.objects.filter(id=self.new_file.guid).exists())
        self.assertFalse(FileFolder.objects.filter(id=self.old_file.guid).exists())

        self.assertFalse(AvatarExport.objects.filter(id=self.unfinished_export.guid).exists())
        self.assertTrue(AvatarExport.objects.filter(id=self.recent_unfinished_export.guid).exists())
