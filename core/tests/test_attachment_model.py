import os

from core.models.attachment import Attachment
from django.core.files.base import ContentFile
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.models import Event
from user.factories import UserFactory
from user.models import User


class AttachmentModelTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

    def attach_file(self, instance, attr, filename):
        setattr(instance, attr, ContentFile("Some content", filename))
        instance.save()
        return getattr(instance, attr).path

    def test_copy_attachment(self):
        event = mixer.blend(Event)
        attachment = mixer.blend(Attachment, attached=event)
        path = self.attach_file(attachment, 'upload', 'testfile.txt')
        self.assertTrue(os.path.isfile(path))  # assert file exists before starting test

        copy = attachment.make_copy(self.authenticatedUser)

        self.assertEqual(copy.owner, self.authenticatedUser)
        self.assertNotEqual(attachment.id, copy.id)
        self.assertNotEqual(copy.id, None)


class TestExifFunctionalityTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner= UserFactory()
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
