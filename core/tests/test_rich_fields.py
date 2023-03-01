import json

from blog.models import Blog
from core.models.attachment import Attachment
from core.models.rich_fields import ReplaceAttachments
from mixer.backend.django import mixer

from tenants.helpers import FastTenantTestCase


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

    def test_links_attachment_with_querystring(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment)

        blog.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}?size=123" }})
        blog.save()

        self.assertTrue(blog.attachments.filter(id=attachment.id).exists())

    def test_links_invalid_uuid(self):
        blog = mixer.blend(Blog)

        blog.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/entity/sdsdsd" }})
        blog.save()

    def test_deleted_when_attached_deleted(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        blog.delete()

        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())

    def test_deleted_when_attached_deleted_wrong_url(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        blog.rich_description = json.dumps({ 'type': 'file', 'attrs': {'url': f"/blabla/{attachment.id}" }})
        blog.delete()

        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())

    def test_replace_attachments(self):
        blog = mixer.blend(Blog)
        attachment_file = mixer.blend(Attachment)
        attachment_image = mixer.blend(Attachment)
        attachment2_file = mixer.blend(Attachment)
        attachment2_image = mixer.blend(Attachment)

        replace_attachment_file = mixer.blend(Attachment)
        replace_attachment_image = mixer.blend(Attachment)
        replace_attachment2_file = mixer.blend(Attachment)
        replace_attachment2_image = mixer.blend(Attachment)

        rich_description = {
            'type': 'doc',
            'content': [
                { 'type': 'image', 'attrs': {'src': f"/attachment/{attachment_image.id}" }},
                { 'type': 'file', 'attrs': {'url': f"/attachment/{attachment_file.id}" }},
                { 'type': 'image', 'attrs': {'src': f"/attachment/entity/{attachment2_image.id}" }},
                { 'type': 'file', 'attrs': {'url': f"/attachment/comment/{attachment2_file.id}" }},
            ]
        }

        blog.rich_description = json.dumps(rich_description)
        blog.save()

        self.assertTrue(blog.attachments.filter(id=attachment_file.id).exists())
        self.assertTrue(blog.attachments.filter(id=attachment_image.id).exists())
        self.assertTrue(blog.attachments.filter(id=attachment2_file.id).exists())
        self.assertTrue(blog.attachments.filter(id=attachment2_image.id).exists())
        self.assertFalse(blog.attachments.filter(id=replace_attachment_file.id).exists())
        self.assertFalse(blog.attachments.filter(id=replace_attachment_image.id).exists())
        self.assertFalse(blog.attachments.filter(id=replace_attachment2_file.id).exists())
        self.assertFalse(blog.attachments.filter(id=replace_attachment2_image.id).exists())

        replace_map = ReplaceAttachments()
        replace_map.append(str(attachment_file.id), str(replace_attachment_file.id))
        replace_map.append(str(attachment_image.id), str(replace_attachment_image.id))
        replace_map.append(str(attachment2_file.id), str(replace_attachment2_file.id))
        replace_map.append(str(attachment2_image.id), str(replace_attachment2_image.id))
        replace_map.replace(blog.replace_attachments(replace_map))
        blog.save()

        self.assertTrue(blog.attachments.filter(id=replace_attachment_file.id).exists())
        self.assertTrue(blog.attachments.filter(id=replace_attachment_image.id).exists())
        self.assertTrue(blog.attachments.filter(id=replace_attachment2_file.id).exists())
        self.assertTrue(blog.attachments.filter(id=replace_attachment2_image.id).exists())
        self.assertFalse(blog.attachments.filter(id=attachment_file.id).exists())
        self.assertFalse(blog.attachments.filter(id=attachment_image.id).exists())
        self.assertFalse(blog.attachments.filter(id=attachment2_file.id).exists())
        self.assertFalse(blog.attachments.filter(id=attachment2_image.id).exists())


