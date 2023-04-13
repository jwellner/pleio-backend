import zipfile
from unittest import mock
from unittest.mock import MagicMock

from django.core.files.base import ContentFile
from django.utils import timezone

from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from core.utils.export.content import ContentSnapshot
from file.factories import FileFactory
from file.models import FileFolder
from user.factories import UserFactory


class TestContentSnapshotTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.CREATED_AT = timezone.datetime.fromisoformat("2000-02-20T23:55:00+01:00")

        self.owner = UserFactory()
        self.attachment = FileFactory(created_at=self.CREATED_AT,
                                      owner=self.owner,
                                      upload=ContentFile(b"content", 'content.jpg'))
        self.blog = BlogFactory(created_at=self.CREATED_AT,
                                title="blog1",
                                rich_description=self.tiptap_attachment(self.attachment),
                                owner=self.owner)
        self.file = FileFactory(created_at=self.CREATED_AT,
                                title="text.txt",
                                owner=self.owner,
                                upload=ContentFile("It's text", "text.txt"))

        self.content_snapshot = ContentSnapshot(self.owner.guid)

    def tearDown(self):
        for file in FileFolder.objects.all():
            file.delete()
        self.blog.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch('core.utils.export.content.BytesIO')
    def test_snapshot_properties(self, create_buffer):
        zip_file = MagicMock()
        buffer = MagicMock()
        create_buffer.return_value = buffer

        folder_name = self.content_snapshot.folder_name(self.blog)
        self.assertTrue(folder_name.startswith(self.blog._meta.label))

        with mock.patch('core.utils.export.content.zipfile.ZipFile') as create_zipfile:
            create_zipfile.return_value = zip_file
            self.content_snapshot.collect_content()

        self.assertEqual(create_zipfile.call_args.args[0], buffer)
        self.assertEqual(create_zipfile.call_args.kwargs, {
            "mode": "w",
            "compression": zipfile.ZIP_DEFLATED,
        })
        self.assertEqual([c.args for c in zip_file.writestr.call_args_list], [
            ('file.FileFolder/2000/02/20/23.55.00/%s/content.jpg' % self.attachment.id, self.attachment.get_media_content()),
            ('blog.Blog/2000/02/20/23.55.00/blog1.html', self.blog.get_media_content()),
            ('blog.Blog/2000/02/20/23.55.00/%s/content.jpg' % self.attachment.id, self.attachment.get_media_content()),
            ('file.FileFolder/2000/02/20/23.55.00/%s/text.txt' % self.file.id, self.file.get_media_content()),
        ])
