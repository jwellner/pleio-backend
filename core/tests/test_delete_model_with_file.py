import os

from core.models.attachment import Attachment
from tenants.helpers import FastTenantTestCase
from django.core.files.base import ContentFile
from mixer.backend.django import mixer
from blog.models import Blog
from file.models import FileFolder

class DeleteAttachmentTestCase(FastTenantTestCase):

    def attach_file(self, instance, attr, filename):
        setattr(instance, attr, ContentFile("Some content", filename))
        instance.save()

        return getattr(instance, attr).path

    def test_delete_removes_file(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)
        path = self.attach_file(attachment, 'upload', 'testfile.txt')
        self.assertTrue(os.path.isfile(path)) # assert file exists before starting test

        attachment.delete()

        self.assertFalse(os.path.exists(path))

    def test_delete_removes_file_from_filefolder(self):
        filefolder = mixer.blend(FileFolder)
        path = self.attach_file(filefolder, 'upload', 'testfile.txt')
        thumbnailPath = self.attach_file(filefolder, 'thumbnail', 'thumbnail.txt')

        filefolder.delete()

        self.assertFalse(os.path.isfile(path))
        self.assertFalse(os.path.isfile(thumbnailPath))

    def test_delete_attachment_and_file(self):
        blog = mixer.blend(Blog)

        attachment = mixer.blend(Attachment, attached=blog)
        path = self.attach_file(attachment, 'upload', 'testfile.txt')
        self.assertTrue(os.path.isfile(path)) # assert file exists before starting test
        self.assertEqual(attachment, Attachment.objects.filter(id=attachment.id).first())

        blog.delete()

        self.assertEqual(None, Attachment.objects.filter(id=attachment.id).first())
        self.assertFalse(os.path.exists(path))
