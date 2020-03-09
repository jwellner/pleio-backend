import os
from django.urls import reverse
from django.db import models
from core.lib import generate_object_filename
from core.models import Entity
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify

def read_access_default():
    return []


def write_access_default():
    return []

class FileFolder(Entity):

    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)

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
            return '{}/files/{}'.format(
                prefix, self.guid
            ).lower()

        return '{}/files/view/{}/{}'.format(
            prefix, self.guid, os.path.basename(self.upload.name)
        ).lower()
    @property
    def download(self):
        return reverse('download', args=[self.id, os.path.basename(self.upload.name)])

    @property
    def thumbnail_url(self):
        return "/file/thumbnail/{}".format(self.id)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False


def set_parent_folders_updated_at(instance):
    if instance.parent and instance.parent.is_folder:
        instance.parent.save()
        set_parent_folders_updated_at(instance.parent)

# TODO: we should get the "real" mime-type of the file. Right now it is send by the user client.
@receiver(pre_save, sender=FileFolder)
def file_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if instance.upload and not instance.title:
        instance.title = instance.upload.file.name
    if instance.upload and not instance.mime_type:
        instance.mime_type = instance.upload.file.content_type

@receiver(post_save, sender=FileFolder)
def file_post_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    set_parent_folders_updated_at(instance)
