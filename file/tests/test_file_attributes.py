import base64
from unittest import mock

from django.utils import timezone

from core.lib import strip_exif
from core.tests.helpers import PleioTenantTestCase
from core.utils import clamav
from core.utils.clamav import FILE_SCAN
from file.models import FileFolder
from user.factories import UserFactory


class TestFileAtrributesTestCase(PleioTenantTestCase):

    @classmethod
    def asset_path(cls, filename):
        return cls.relative_path(__file__, ['assets', filename])

    def test_get_file_content(self):
        file = self.file_factory(self.asset_path('upload.txt'))
        self.assertEqual(file.get_content().decode(), 'Demo upload file.')
        self.assertEqual(file.get_content(
            wrap=base64.encodebytes).decode(), 'RGVtbyB1cGxvYWQgZmlsZS4=\n')

    def test_load_file_by_path(self):
        file1 = self.file_factory(self.asset_path('grass.jpg'))
        file2 = self.file_factory(self.asset_path('navy.jpg'))
        file3 = self.file_factory(self.asset_path('piggy.jpg'))
        file4 = self.file_factory(self.asset_path('upload.txt'))

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

    @mock.patch('core.utils.clamav.scan')
    @mock.patch('file.models.ScanIncidentManager.create_from_file_folder')
    def test_scan_file_clean(self, mocked_create_incident, mocked_scan):
        mocked_scan.return_value = FILE_SCAN.CLEAN
        start_date_time = timezone.now()
        file: FileFolder = self.file_factory(self.asset_path('grass.jpg'))

        result = file.scan()
        file.refresh_from_db()

        self.assertTrue(result)
        self.assertTrue(file.last_scan >= start_date_time)
        self.assertTrue(file.last_scan <= timezone.now())
        self.assertTrue(mocked_scan.called)
        self.assertFalse(mocked_create_incident.called)

    @mock.patch('core.utils.clamav.scan')
    @mock.patch('file.models.ScanIncidentManager.create_from_file_folder')
    def test_scan_file_with_virus(self, mocked_create_incident, mocked_scan):
        mocked_scan.side_effect = clamav.FileScanError(FILE_SCAN.VIRUS, "NL.SARS.PLEIO.Z665")
        start_date_time = timezone.now()
        file: FileFolder = self.file_factory(self.asset_path('grass.jpg'))

        result = file.scan()
        file.refresh_from_db()

        self.assertFalse(result)
        self.assertTrue(file.last_scan >= start_date_time)
        self.assertTrue(file.last_scan <= timezone.now())
        self.assertTrue(mocked_scan.called)
        self.assertTrue(mocked_create_incident.called)




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
