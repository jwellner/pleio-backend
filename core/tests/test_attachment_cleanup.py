from mixer.backend.django import mixer
from django.db import connection
from core.tasks.cronjobs import remove_floating_attachments
from core.models.attachment import Attachment
from blog.models import Blog
from tenants.helpers import FastTenantTestCase


class AttachmentCleanupTestcase(FastTenantTestCase):
    def test_deletes_floating(self):
        attachment = mixer.blend(Attachment)

        remove_floating_attachments.s(connection.schema_name).apply()

        self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())

    def test_keeps_non_floating(self):
        blog = mixer.blend(Blog)
        attachment = mixer.blend(Attachment, attached=blog)

        remove_floating_attachments.s(connection.schema_name).apply()

        self.assertTrue(Attachment.objects.filter(id=attachment.id).exists())
