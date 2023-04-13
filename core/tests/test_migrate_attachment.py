import json
import os

from mixer.backend.django import mixer

from blog.factories import BlogFactory
from core.models import Attachment, ResizedImage
from core.post_deploy.translate_attachment_to_filefolder import migrate_attachment
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import UserFactory


class TestMigrateAttachmentTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.demo_file_path = self.relative_path(__file__, ['assets', 'landscape.jpeg'])
        self.attachment: Attachment = mixer.blend(Attachment,
                                      owner=self.owner,
                                      upload=self.build_contentfile(self.demo_file_path))
        self.resized_image = self.attachment.resized_images.create(
            upload=self.build_contentfile(self.demo_file_path),
            size=100,
            mime_type=self.attachment.mime_type,
            status=ResizedImage.OK,
        )

        self.blog = BlogFactory(owner=self.owner,
                                rich_description=json.dumps(
                                    {'type': 'doc',
                                     'content': [{'type': 'file',
                                                  'attrs': {'guid': None,
                                                            'url': self.attachment.url,
                                                            'name': self.attachment.name,
                                                            'mimeType': self.attachment.mime_type,
                                                            'size': self.attachment.size}}
                                                 ]
                                     }
                                ))
        self.attachment.attached = self.blog
        self.attachment.save()

    def tearDown(self):
        for attachment in Attachment.objects.all():
            attachment.delete()

        for file in FileFolder.objects.all():
            file.delete()

        self.blog.delete()
        self.owner.delete()

    def test_migrate_attachment(self):
        expected = {
            'id': self.attachment.id,
            'title': self.attachment.name,
            'created_at': self.attachment.created_at,
            'owner': self.attachment.owner,
            'mime_type': self.attachment.mime_type,
        }
        original_file_location = self.attachment.upload.path
        expected_content = open(self.attachment.upload.path, 'rb').read()
        expected_resized = [str(pk) for pk in self.attachment.resized_images.get_queryset().values_list('id', flat=True)]

        new_file = migrate_attachment(self.attachment.guid)
        actual_content = open(new_file.upload.path, 'rb').read()
        actual_resized = [str(pk) for pk in new_file.resized_images.get_queryset().values_list('id', flat=True)]

        for field, value in expected.items():
            self.assertEqual(getattr(new_file, field), value, msg="Mismatch at %s. Expected %s but found %s" % (field, value, getattr(new_file, field)))

        self.assertTrue(new_file.updated_at > new_file.created_at)
        self.assertEqual(new_file.upload.path, original_file_location)
        self.assertEqual(actual_content, expected_content)
        self.assertTrue(os.path.exists(original_file_location))
        self.assertTrue(FileFolder.objects.filter(id=expected['id']).exists())
        self.assertTrue(self.blog.attachments.filter(file_id=expected['id']).exists())
        self.assertEqual(expected_resized, actual_resized)
        self.assertFalse(Attachment.objects.filter(id=expected['id']).exists())

