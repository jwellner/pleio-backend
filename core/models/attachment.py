import uuid
import os
import logging
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from core.lib import get_mimetype
from core.models.mixin import ModelWithFile

logger = logging.getLogger(__name__)

def attachment_path(instance, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join('attachments', str(instance.id), filename)

class Attachment(ModelWithFile):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256, default="")
    upload = models.FileField(upload_to=attachment_path, blank=True, null=True, max_length=512)
    mime_type = models.CharField(null=True, blank=True, max_length=100)
    size = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    attached_content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    attached_object_id = models.UUIDField(blank=True, null=True)
    attached = GenericForeignKey(ct_field='attached_content_type', fk_field='attached_object_id')

    def can_read(self, user):
        if not hasattr(self.attached, 'can_read'):
            return True # Groups don't have the function implemented

        return self.attached.can_read(user)

    @property
    def type(self):
        return self.attached_content_type.model

    @property
    def url(self):
        return reverse('attachment', args=[self.id])

    @property
    def file_fields(self):
        return [self.upload]

    def __str__(self):
        return f"{self._meta.object_name}[{self.upload.name}]"

@receiver(models.signals.pre_save, sender=Attachment)
def attachment_mimetype_size(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if settings.IMPORTING:
        return
    if instance.upload and not instance.name:
        instance.name = instance.upload.file.name
    if instance.upload:
        instance.mime_type = get_mimetype(instance.upload.path)
        try:
            instance.size = instance.upload.size
        except Exception:
            pass
