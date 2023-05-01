import json

from blog.factories import BlogFactory
from core.models.rich_fields import ReplaceAttachments
from core.tests.helpers import PleioTenantTestCase
from file.models import FileReference
from user.factories import UserFactory


class RichFieldTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.blog = BlogFactory(owner=self.owner)
        self.file = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                      owner=self.owner)

    def assertFileReferenceNotExists(self, file, container, msg=None):
        self.assertFalse(FileReference.objects.filter(container_fk=container.id, file=file).exists(), msg=msg)

    def assertFileReferenceExists(self, file, container, msg=None):
        self.assertTrue(FileReference.objects.filter(container_fk=container.id, file=file).exists(), msg=msg)

    def test_removes_attachment(self):
        FileReference.objects.get_or_create(file=self.file, container=self.blog)

        self.blog.rich_description = json.dumps({})
        self.blog.save()

        self.assertFileReferenceNotExists(self.file, self.blog)

    def test_keeps_attachment(self):
        self.blog.rich_description = json.dumps({'type': 'file', 'attrs': {'url': f"/attachment/entity/{self.file.id}"}})
        self.blog.save()

        self.assertFileReferenceExists(self.file, self.blog)

    def test_links_attachment(self):
        self.blog.rich_description = json.dumps({'type': 'file', 'attrs': {'url': f"/attachment/entity/{self.file.id}"}})
        self.blog.save()

        self.assertTrue(self.blog.attachments.filter(file_id=self.file.id).exists())

    def test_links_attachment_with_querystring(self):
        self.blog.rich_description = json.dumps({'type': 'file', 'attrs': {'url': f"/attachment/entity/{self.file.id}?size=123"}})
        self.blog.save()

        self.assertFileReferenceExists(self.file, self.blog)

    def test_links_invalid_uuid(self):
        self.blog.rich_description = json.dumps({'type': 'file', 'attrs': {'url': f"/attachment/entity/sdsdsd"}})
        self.blog.save()

        self.assertFileReferenceNotExists(self.file, self.blog)

    def test_deleted_when_attached_deleted_file_url(self):
        self.blog.rich_description = json.dumps({'type': 'file', 'attrs': {'url': f"/blabla/{self.file.id}"}})
        self.blog.save()

        self.assertFileReferenceExists(self.file, self.blog)

    def test_replace_attachments(self):
        file1 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        file2 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        file3 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        file4 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)

        replace1 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        replace2 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        replace3 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)
        replace4 = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']), owner=self.owner)

        rich_description = {
            'type': 'doc',
            'content': [
                {'type': 'image', 'attrs': {'src': f"/attachment/{file1.id}"}},
                {'type': 'file', 'attrs': {'url': f"/attachment/{file2.id}"}},
                {'type': 'image', 'attrs': {'src': f"/attachment/entity/{file3.id}"}},
                {'type': 'file', 'attrs': {'url': f"/attachment/comment/{file4.id}"}},
            ]
        }

        self.blog.rich_description = json.dumps(rich_description)
        self.blog.save()

        self.assertFileReferenceExists(file1, self.blog)
        self.assertFileReferenceExists(file2, self.blog)
        self.assertFileReferenceExists(file3, self.blog)
        self.assertFileReferenceExists(file4, self.blog)
        self.assertFileReferenceNotExists(replace1, self.blog)
        self.assertFileReferenceNotExists(replace2, self.blog)
        self.assertFileReferenceNotExists(replace3, self.blog)
        self.assertFileReferenceNotExists(replace4, self.blog)

        replace_map = ReplaceAttachments()
        replace_map.append(file1.guid, replace1.guid)
        replace_map.append(file2.guid, replace2.guid)
        replace_map.append(file3.guid, replace3.guid)
        replace_map.append(file4.guid, replace4.guid)
        self.blog.replace_attachments(replace_map)
        self.blog.save()

        self.assertFileReferenceNotExists(file1, self.blog)
        self.assertFileReferenceNotExists(file2, self.blog)
        self.assertFileReferenceNotExists(file3, self.blog)
        self.assertFileReferenceNotExists(file4, self.blog)
        self.assertFileReferenceExists(replace1, self.blog)
        self.assertFileReferenceExists(replace2, self.blog)
        self.assertFileReferenceExists(replace3, self.blog)
        self.assertFileReferenceExists(replace4, self.blog)
