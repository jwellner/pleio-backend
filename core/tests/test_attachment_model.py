import os
from core.models.attachment import Attachment
from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from mixer.backend.django import mixer
from event.models import Event
from user.models import User

class AttachmentModelTestCase(FastTenantTestCase):
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
        self.assertTrue(os.path.isfile(path)) # assert file exists before starting test
        
        copy = attachment.make_copy(self.authenticatedUser)

        self.assertEqual(copy.owner, self.authenticatedUser)
        self.assertNotEqual(attachment.id, copy.id)
        self.assertNotEqual(copy.id, None)
