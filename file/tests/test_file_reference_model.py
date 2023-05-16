from django.core.files.base import ContentFile

from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory
from file.models import FileReference
from user.factories import UserFactory


class TestFileReferenceModelTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.file = FileFactory(owner=self.owner,
                                upload=ContentFile("Test!\n", "testfile.txt"))

    def tearDown(self):
        super().tearDown()

    def test_delete_container_deletes_relation(self):
        blog = BlogFactory(owner=self.owner)
        FileReference.objects.get_or_create(file=self.file, container=blog)
        self.assertEqual(self.file.referenced_by.count(), 1)

        blog.delete()

        self.assertEqual(self.file.referenced_by.count(), 0)
