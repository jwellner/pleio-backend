from unittest import mock

from core.factories import AttachmentFactory, GroupFactory
from core.models.attachment import Attachment

from core.tests.helpers import PleioTenantTestCase
from core.utils.clamav import FILE_SCAN, FileScanError
from event.factories import EventFactory
from user.factories import UserFactory


class AttachmentModelTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = UserFactory()
        self.event = EventFactory(owner=self.authenticatedUser)
        self.attachment = AttachmentFactory(
            upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'landscape.jpeg'])),
            attached=self.event,
        )

    def tearDown(self):
        self.attachment.delete()
        self.event.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_copy_attachment(self):
        copy = self.attachment.make_copy(self.authenticatedUser)

        self.assertEqual(copy.owner, self.authenticatedUser)
        self.assertNotEqual(self.attachment.id, copy.id)
        self.assertNotEqual(copy.id, None)

    @mock.patch('core.utils.clamav.scan')
    @mock.patch('file.models.ScanIncidentManager.create_from_attachment')
    def test_scan_attachment(self, mocked_create, mocked_scan):
        mocked_scan.return_value = FILE_SCAN.CLEAN

        result = self.attachment.scan()
        self.assertTrue(result)
        self.assertTrue(mocked_scan.called)
        self.assertFalse(mocked_create.called)

    @mock.patch('core.utils.clamav.scan')
    @mock.patch('file.models.ScanIncidentManager.create_from_attachment')
    def test_scan_attachment_with_virus(self, mocked_create, mocked_scan):
        mocked_scan.side_effect = FileScanError(FILE_SCAN.VIRUS, "NLSARS.PLEIO.664")

        result = self.attachment.scan()
        self.assertFalse(result)
        self.assertTrue(mocked_scan.called)
        self.assertTrue(mocked_create.called)

    def test_no_group_property(self):
        self.assertIsNone(self.attachment.group)

    def test_nothing_attached_group_property(self):
        self.attachment.attached = None
        self.attachment.save()

        self.assertIsNone(self.attachment.group)

    def test_entity_group_property(self):
        group = GroupFactory(owner=self.authenticatedUser)
        self.event.group = group
        self.event.save()

        self.assertEqual(self.attachment.group, group)

    def test_group_property(self):
        group = GroupFactory(owner=self.authenticatedUser)
        self.attachment.attached = group
        self.attachment.save()

        self.assertEqual(self.attachment.group, group)

    def test_group_invalid_property(self):
        self.attachment.attached = UserFactory()
        self.attachment.save()

        self.assertIsNone(self.attachment.group)

    def test_guid_property(self):
        self.assertIsInstance(self.attachment.guid, str)
        self.assertEqual(self.attachment.guid, str(self.attachment.id))


    def test_standard_filename(self):
        file: Attachment = AttachmentFactory(
            upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'avatar.jpg'])),
            name='avatar.jpg',
            attached=self.authenticatedUser
        )
        self.assertEqual(file.clean_filename(), "avatar.jpg")

        file.name = "Something else.jpg"
        self.assertEqual(file.clean_filename(), 'something-else.jpg')

        file.name = "Something else.JPG"
        self.assertEqual(file.clean_filename(), 'something-else.jpg')

        file.name = "Something else"
        self.assertEqual(file.clean_filename(), 'something-else.jpg')

        file.name = "Another ext.jpeg"
        self.assertEqual(file.clean_filename(), 'another-ext.jpg')


class TestExifFunctionalityTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.attachment = Attachment(
            owner=self.owner,
            upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'exif_example.jpg'])),
            mime_type='image/jpeg',
        )

    def tearDown(self):
        self.attachment.delete()
        super().tearDown()

    def test_strip_exif(self):
        # Given
        self.assertExif(self.attachment.upload.file)

        # When
        self.attachment.save()

        # Then
        self.assertNotExif(self.attachment.upload.file)
