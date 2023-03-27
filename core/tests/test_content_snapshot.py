import zipfile
from unittest import mock
from unittest.mock import MagicMock

from django.core.files.base import ContentFile
from django.utils import timezone

from blog.factories import BlogFactory
from core.factories import AttachmentFactory
from core.tests.helpers import PleioTenantTestCase
from core.utils.export.content import ContentSnapshot
from file.factories import FileFactory
from user.factories import UserFactory


class TestContentSnapshotTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.CREATED_AT = timezone.datetime(year=2000, month=2, day=20,
                                            hour=23, minute=55, second=0)

        self.owner = UserFactory()
        self.blog = BlogFactory(created_at=self.CREATED_AT,
                                title="blog1",
                                rich_description="Some description",
                                owner=self.owner)
        self.attachment = AttachmentFactory(created_at=self.CREATED_AT,
                                            attached=self.blog,
                                            upload=ContentFile(b"content", 'content.jpg'))
        self.file = FileFactory(created_at=self.CREATED_AT,
                                title="text.txt",
                                owner=self.owner,
                                upload=ContentFile("It's text", "text.txt"))

        self.content_snapshot = ContentSnapshot(self.owner.guid)

    def tearDown(self):
        self.file.delete()
        self.attachment.delete()
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
            ('blog.Blog/2000/02/20/23.55.00/blog1.html', 'Some description'),
            ('blog.Blog/2000/02/20/23.55.00/%s.jpg' % self.attachment.id, b'content'),
            ('file.FileFolder/2000/02/20/23.55.00/text.txt', b"It's text"),
        ])
