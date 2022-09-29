import os

from core.models.attachment import Attachment
from django.core.files import File
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.models import Event
from user.factories import UserFactory
from user.models import User


class AttachmentModelTestCase(PleioTenantTestCase):
    basepath = 'test_files/'

    def setUp(self):
        self.authenticatedUser = mixer.blend(User)
        os.makedirs(self.basepath, exist_ok=True)

    def tearDown(self):
        os.system(f"rm -r {self.basepath}")

    def attach_file(self, instance, attr, filename):
        path = self.basepath + filename
        with open(path, 'w+') as f:
            file = File(f)
            file.write("some content")
            setattr(instance, attr, file)
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
