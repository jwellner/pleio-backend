from django.db import models
from core.lib import generate_object_filename
from core.models import Entity
from django.db.models.signals import pre_save
from django.dispatch import receiver

def read_access_default():
    return []


def write_access_default():
    return []

class FileFolder(Entity):

    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)

    def type_to_string(self):
        if self.is_folder:
            return 'folder'
        return 'file'

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

# TODO: we should get the "real" mime-type of the file. Right now it is send by the user client.
@receiver(pre_save, sender=FileFolder)
def file_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if instance.upload and not instance.title:
        instance.title = instance.upload.file.name
    if instance.upload and not instance.mime_type:
        instance.mime_type = instance.upload.file.content_type