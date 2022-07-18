import base64
import os.path

from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder


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

