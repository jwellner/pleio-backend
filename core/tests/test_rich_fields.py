import json

from blog.models import Blog
from core.models.attachment import Attachment
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

class RichFieldTestCase(FastTenantTestCase):
    def test_removes_attachment(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        blog.rich_description = json.dumps({})
        blog.save()

        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())

    def test_keeps_attachment(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        blog.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}" }})
        blog.save()

        self.assertTrue(Attachment.objects.filter(id=attachment.id).exists())

    def test_links_attachment(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment)

        blog.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}" }})
        blog.save()

        self.assertTrue(blog.attachments.filter(id=attachment.id).exists())

    def test_deleted_when_attached_deleted(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        blog.delete()

        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())
