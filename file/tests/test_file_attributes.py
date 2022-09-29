import base64
import os.path

from core.lib import strip_exif
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import UserFactory


class TestFileAtrributesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

    def relative_path(self, filename):
        return os.path.join(os.path.dirname(__file__), 'assets', filename)

    def test_get_file_content(self):
        file = self.file_factory(self.relative_path('upload.txt'))
        self.assertEqual(file.get_content().decode(), 'Demo upload file.')
        self.assertEqual(file.get_content(
            wrap=base64.encodebytes).decode(), 'RGVtbyB1cGxvYWQgZmlsZS4=\n')

    def test_load_file_by_path(self):
        file1 = self.file_factory(self.relative_path('grass.jpg'))
        file2 = self.file_factory(self.relative_path('navy.jpg'))
        file3 = self.file_factory(self.relative_path('piggy.jpg'))
        file4 = self.file_factory(self.relative_path('upload.txt'))

        found = []
        expected = []
        for file, description in [(file1, "grass.jpg"),
                                  (file2, "navy.jpg"),
                                  (file3, "piggy.jpg"),
                                  (file4, "upload.txt")]:
            expected.append(file)
            found.append(FileFolder.objects.file_by_path(file.upload.path))

        self.assertEqual([(p.id, p.upload.name) for p in expected],
                         [(p.id, p.upload.name) for p in found])


class TestExifTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()

    def test_text_file_exif(self):
        # given
        file: FileFolder = FileFolder.objects.create(owner=self.owner,
                                                     upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'upload.txt'])),
                                                     mime_type='text/plain')
        strip_exif(file.upload)
        file.refresh_from_db()

        self.assertNotExif(file.upload.file)

    def test_image_file_exif(self):
        file: FileFolder = FileFolder.objects.create(owner=self.owner,
                                                     upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'avatar-with-exif.jpg'])),
                                                     mime_type='image/jpeg')

        # when
        strip_exif(file.upload)
        file.refresh_from_db()

        self.assertNotExif(file.upload.file)
