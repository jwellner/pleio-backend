import abc
import os
import logging
import celery
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from core.models.mixin import ModelWithFile
from core.lib import tenant_schema

VALID_IMAGE_SIZES = [360, 414, 660, 1040]

logger = logging.getLogger(__name__)

def image_path(instance, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = "%i_%s.%s" % (instance.size, slugify(name), ext)
    return os.path.join('images', str(instance.original.id), filename)

class ResizedImage(ModelWithFile):

    OK = 'OK'
    PENDING = 'PENDING'
    FAILED = 'FAILED'

    original_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    original_object_id = models.UUIDField()
    original = GenericForeignKey(ct_field='original_content_type', fk_field='original_object_id')

    upload = models.FileField(upload_to=image_path, max_length=512)
    size = models.IntegerField()
    mime_type = models.CharField(null=True, blank=True, max_length=100)

    status = models.CharField(max_length=255, default=PENDING)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def file_fields(self):
        return [self.upload]

    @property
    def name(self):
        return os.path.basename(self.upload.name)

class ResizedImageMixin(models.Model):
    class Meta:
        abstract = True

    resized_images = GenericRelation(ResizedImage, object_id_field='original_object_id', content_type_field='original_content_type')

    @property
    @abc.abstractmethod
    def upload_field(self):
        """ Return FileField with image """

    @property
    @abc.abstractmethod
    def mime_type_field(self):
        """ Return mime_type field """

    def is_image(self):
        return str(self.mime_type_field).startswith('image/')

    def get_resized_image(self, size):
        if not self.is_image():
            return None

        try:
            size = int(size)
        except ValueError:
            return None

        if size not in VALID_IMAGE_SIZES:
            logger.info("Invalid size %i requested for image %s", size, self)
            return None

        image = self.resized_images.filter(size=size).first()

        if not image:
            tmp_img = ResizedImage.objects.create(
                size=size,
                original=self
            )

            celery.current_app.send_task('core.tasks.misc.image_resize', (tenant_schema(), tmp_img.id,))

        if image and image.status == ResizedImage.OK:
            return image

        return None
