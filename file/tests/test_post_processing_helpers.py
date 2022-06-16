from unittest import mock

from django.conf import settings
from django.core.files import File

from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestPostProcessingHelpersTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestPostProcessingHelpersTestCase, self).setUp()
        from file.models import FileFolder

        self.file_mock = mock.MagicMock(spec=File)
        self.file_mock.name = 'icon-name.jpg'
        self.file_mock.title = 'icon-name.jpg'
        self.file_mock.content_type = 'image/jpeg'
        self.file_mock.size = 123

        self.user = UserFactory()

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.user.id)],
            write_access=[ACCESS_TYPE.user.format(self.user.id)],
            owner=self.user,
            upload=self.file_mock,
            title=self.file_mock.title
        )

        self.Model = FileFolder

    @mock.patch("file.models.is_upload_complete")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_model_post_save_works(self, mock_open, mock_is_upload_complete):
        mock_open.return_value = self.file_mock
        mock_is_upload_complete.return_value = True

        self.file.title = "some-other-title"
        self.file.save()

        assert mock_is_upload_complete.called, 'file_post_save not called'

    @mock.patch("file.models.is_upload_complete")
    @mock.patch("core.lib.get_basename")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_invalid_filename(self, mock_open, mock_filename, mock_post_save):
        from file.validators import valid_filename
        from file.helpers.post_processing import ensure_correct_file_without_signals

        mock_open.return_value = self.file_mock
        mock_filename.return_value = self.file_mock.name
        self.Model.objects.filter(id=self.file.id).update(title='')
        self.file.refresh_from_db()

        self.assertFalse(valid_filename(self.file.title))
        ensure_correct_file_without_signals(self.file)

        self.assertEqual(self.file.title, self.file_mock.name)
        assert not mock_post_save.called, "Signals still triggered"

    @mock.patch("file.models.is_upload_complete")
    @mock.patch("core.lib.get_mimetype")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_invalid_mimetype(self, mock_open, mock_mimetype, mock_post_save):
        from file.validators import valid_mimetype
        from file.helpers.post_processing import ensure_correct_file_without_signals

        mock_open.return_value = self.file_mock
        mock_mimetype.return_value = self.file_mock.content_type
        self.Model.objects.filter(id=self.file.id).update(mime_type='')
        self.file.refresh_from_db()

        self.assertFalse(valid_mimetype(self.file.mime_type))
        ensure_correct_file_without_signals(self.file)

        self.assertEqual(self.file.mime_type, self.file_mock.content_type)
        assert not mock_post_save.called, "Signals still triggered"

    @mock.patch("file.models.is_upload_complete")
    @mock.patch("os.path.getsize")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_invalid_size(self, mock_open, mock_filesize, mock_post_save):
        from file.validators import valid_filesize
        from file.helpers.post_processing import ensure_correct_file_without_signals

        mock_open.return_value = self.file_mock
        mock_filesize.return_value = self.file_mock.size
        self.Model.objects.filter(id=self.file.id).update(size=0)
        self.file.refresh_from_db()

        self.assertFalse(valid_filesize(self.file.size))
        ensure_correct_file_without_signals(self.file)

        self.assertEqual(self.file.size, self.file_mock.size)
        assert not mock_post_save.called, "Signals still triggered"
