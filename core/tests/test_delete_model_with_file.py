import os
from core.models.attachment import Attachment
from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from django.conf import settings
from mixer.backend.django import mixer
from blog.models import Blog
from file.models import FileFolder

class DeleteAttachmentTestCase(FastTenantTestCase):
    basepath = 'test_files/'

    def setUp(self):
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
