import uuid
import os
import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.urls import reverse

from core.lib import get_mimetype, strip_exif, get_basename, tenant_schema
from core.models.mixin import ModelWithFile, HasMediaMixin
from core.models.image import ResizedImageMixin
from core.utils import clamav

logger = logging.getLogger(__name__)


class AttachmentQuerySet(models.QuerySet):
    def filter_attached(self, obj):
        return self.filter(attached_object_id=obj.id,
                           attached_content_type=ContentType.objects.get_for_model(obj).pk)


def attachment_path(instance, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%s.%s" % (slugify(name), ext)
    return os.path.join('attachments', str(instance.id), filename)


class Attachment(ModelWithFile, ResizedImageMixin, HasMediaMixin):
    objects = AttachmentQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256, default="")
    upload = models.FileField(upload_to=attachment_path, blank=True, null=True, max_length=512)
    mime_type = models.CharField(null=True, blank=True, max_length=100)
    size = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey('user.User', on_delete=models.PROTECT)

    attached_content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    attached_object_id = models.UUIDField(blank=True, null=True)
    attached = GenericForeignKey(ct_field='attached_content_type', fk_field='attached_object_id')

    last_scan = models.DateTimeField(default=timezone.now)
    blocked = models.BooleanField(default=False)
    block_reason = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        created = self._state.adding
        self.update_metadata()
        super(Attachment, self).save(*args, **kwargs)
        self.strip_exif_on_add(created)

    def scan(self):
        try:
            clamav.scan(self.upload.path)
            return True
        except AttributeError:
            return False
        except clamav.FileScanError as e:
            from file.models import ScanIncident
            ScanIncident.objects.create_from_attachment(e, self)
            return not e.is_virus()

    @property
    def group(self):
        try:
            if self.attached._meta.label == 'core.Group':
                return self.attached
            return self.attached.group
        except AttributeError:
            return None

    @property
    def guid(self):
        return str(self.id)

    def update_metadata(self):
        if self.upload:
            try:
                if not self.name:
                    self.name = get_basename(self.upload.name)
                self.mime_type = get_mimetype(self.upload.path)
                self.size = self.upload.size
            except FileNotFoundError:
                pass

    def strip_exif_on_add(self, created):
        if created and self.is_image():
            strip_exif(self.upload)

    def can_read(self, user):
        if not self.attached:
            return user == self.owner

        if not hasattr(self.attached, 'can_read'):
            return True  # Groups don't have the function implemented

        return self.attached.can_read(user)

    def make_copy(self, user):
        new = Attachment()
        new_file = ContentFile(self.upload.read())
        new_file.name = self.upload.name
        new.upload = new_file
        new.owner = user

        new.save()

        return new

    @property
    def type(self):
        return self.attached_content_type.model

    @property
    def url(self):
        return reverse('attachment', args=[self.id])

    @property
    def file_fields(self):
        return [self.upload]

    @property
    def upload_field(self):
        return self.upload

    @property
    def mime_type_field(self):
        return self.mime_type

    def __str__(self):
        return f"{self._meta.object_name}[{self.upload.name}]"

    def get_media_status(self):
        try:
            with open(self.upload.path, 'r'):
                return True
        except Exception:
            return False

    def get_media_filename(self):
        name, ext = os.path.splitext(self.upload.path)
        return "%s%s" % (self.pk, ext)

    def get_media_content(self):
        with open(self.upload.path, 'rb') as fh:
            return fh.read()
