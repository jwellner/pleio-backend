import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.lib import get_acl, generate_object_filename
from .shared import read_access_default, write_access_default

class FileFolderManager(models.Manager):
    def visible(self, user):
        qs = self.get_queryset()
        if user.is_authenticated and user.is_admin:
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))

class FileFolder(models.Model):
    objects = FileFolderManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('core.User', on_delete=models.PROTECT)
    group = models.ForeignKey(
        'core.Group',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    read_access = ArrayField(
        models.CharField(max_length=64),
        blank=True,
        default=read_access_default
    )
    write_access = ArrayField(
        models.CharField(max_length=64),
        blank=True,
        default=write_access_default
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True)
    content_type = models.CharField(null=True, blank=True, max_length=100)

    @property
    def guid(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        if self.upload:
            self.content_type = self.upload.file.content_type
        super().save(*args, **kwargs)
