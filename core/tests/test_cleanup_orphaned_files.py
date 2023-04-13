import os

from django.utils.timezone import timedelta

from core.tasks.cronjobs import cleanup_orphaned_files
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import UserFactory


class TestAvatarExportCleanupTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.new_file = self.file_factory(self.relative_path(__file__, ['assets', 'avatar_export.zip']))
        self.old_file = self.file_factory(self.relative_path(__file__, ['assets', 'avatar_export.zip']))

        FileFolder.objects.filter(id=self.old_file.id).update(created_at=self.old_file.created_at - timedelta(days=31))

    def tearDown(self):
        for file in FileFolder.objects.all():
            file.delete()
        super().tearDown()

    def test_remove_exports(self):
        # Given
        self.assertTrue(os.path.exists(self.new_file.upload.path))
        self.assertTrue(os.path.exists(self.old_file.upload.path))

        # When
        cleanup_orphaned_files(self.tenant.schema_name)

        # Then
        self.assertTrue(os.path.exists(self.new_file.upload.path))
        self.assertFalse(os.path.exists(self.old_file.upload.path))

