import os
import mimetypes
from auditlog.registry import auditlog
from django.urls import reverse
from django.conf import settings
from django.db import models
from core.lib import generate_object_filename
from core.models import Entity
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify

def read_access_default():
    return []


def write_access_default():
    return []


def get_mimetype(file):
    """
    Get mimetype by reading the header of the file
    """
    mime_type, _ = mimetypes.guess_type(file.upload.path)
    if not mime_type:
        return None
    return mime_type


class FileFolder(Entity):

    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True, max_length=512)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return f"FileFolder[{self.title}]"

    @property
    def type_to_string(self):
        if self.is_folder:
            return 'folder'
        return 'file'

    @property
    def url(self):
        prefix = ''

        if self.is_folder:
            if self.group:
                prefix = '/groups/view/{}/{}'.format(
                    self.group.guid, slugify(self.group.name)
                )
            else: # personal file browser url
                prefix = '/user/{}'.format(self.owner.guid)

            return '{}/files/{}'.format(
                prefix, self.guid
            ).lower()

        return '{}/files/view/{}/{}'.format(
            prefix, self.guid, os.path.basename(self.upload.name)
        ).lower()
    @property
    def download_url(self):
        return reverse('download', args=[self.id, os.path.basename(self.upload.name)])

    @property
    def embed_url(self):
        return reverse('embed', args=[self.id, os.path.basename(self.upload.name)])

    @property
    def thumbnail_url(self):
        return reverse('thumbnail', args=[self.id])

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False


def set_parent_folders_updated_at(instance):
    if instance.parent and instance.parent.is_folder:
        instance.parent.save()
        set_parent_folders_updated_at(instance.parent)

@receiver(pre_save, sender=FileFolder)
def file_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if settings.IMPORTING:
        return
    if instance.upload and not instance.title:
        instance.title = instance.upload.file.name
    if instance.upload:
        instance.mime_type = get_mimetype(instance)

# update parent folders updated_at when adding, moving and deleting files
@receiver([pre_save, pre_delete], sender=FileFolder)
def update_parent_timestamps(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if settings.IMPORTING:
        return

    set_parent_folders_updated_at(instance)

    try:
        # Also update old parent if changed
        old_instance = FileFolder.objects.get(id=instance.id)
        if old_instance.parent != instance.parent:
            set_parent_folders_updated_at(old_instance)
    except ObjectDoesNotExist:
        pass


auditlog.register(FileFolder)