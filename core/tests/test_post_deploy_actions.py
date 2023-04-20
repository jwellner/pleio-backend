import json

from django.core.files.base import ContentFile

from blog.factories import BlogFactory
from core.models import Revision
from core.post_deploy.translate_attachment_to_filefolder import migrate_revision, task
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMigrateRevisionAttachmentsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.inline_attachment = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                                   owner=self.owner)
        self.featured_image = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                                owner=self.owner)
        self.blog = BlogFactory(owner=self.owner,
                                rich_description=self.tiptap_attachment(self.inline_attachment),
                                featured_image=self.featured_image)
        self.revision = Revision.objects.create(author=self.owner,
                                                _container=self.blog,
                                                unchanged=self.blog.serialize())

    def tearDown(self):
        self.revision.delete()
        self.blog.delete()
        self.featured_image.delete()
        self.inline_attachment.delete()
        self.owner.delete()
        super().tearDown()

    def test_migrate_revision(self):
        migrate_revision(self.revision)

        self.assertEqual({*self.revision.attachments}, {
            self.featured_image.guid,
            self.inline_attachment.guid,
        })


class TestTaskTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.owner = UserFactory()

        self.attachments = [
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
            self.create_blog_with_attachment(),
        ]

    def create_blog_with_attachment(self):
        from core.models import Attachment
        attachment = Attachment.objects.create(name='some file.jpg',
                                               owner=self.owner,
                                               upload=ContentFile(b"content", 'some-file.jpg'))
        blog = BlogFactory(owner=self.owner,
                           rich_description=json.dumps({
                               'type': 'doc',
                               'content': [{'type': 'file', 'attrs': {'guid': None,
                                                                      'url': attachment.url,
                                                                      'name': attachment.name,
                                                                      'mimeType': attachment.mime_type,
                                                                      'size': attachment.size,
                                                                      }}]}))
        attachment.attached = blog
        attachment.save()
        return blog

    def test_task(self):
        task()
