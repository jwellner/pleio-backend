import os

from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder, FileReference
from user.factories import UserFactory


class DeleteAttachmentTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.blog = BlogFactory(owner=self.owner)
        self.file = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                      owner=self.owner)
        self.reference, _ = FileReference.objects.get_or_create(container=self.blog, file=self.file)
        self.path = self.file.upload.path

    def test_delete_file(self):
        self.assertTrue(os.path.isfile(self.path))  # assert file exists before starting test

        self.file.delete()

        self.assertFalse(os.path.exists(self.path))

    def test_delete_blog(self):
        self.assertTrue(os.path.isfile(self.path))
        self.assertTrue(FileReference.objects.filter(container_fk=self.blog.id).exists())

        self.blog.delete()

        self.assertFalse(FileReference.objects.filter(container_fk=self.blog.id).exists())
        self.assertTrue(os.path.isfile(self.path))
        self.assertEqual([*FileFolder.objects.filter_orphaned_files()], [self.file])
