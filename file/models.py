import os
import clamd
import logging
import signal_disabler

from auditlog.registry import auditlog
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.utils import timezone
from enum import Enum
from core.lib import generate_object_filename, get_mimetype, tenant_schema, get_basename, get_filesize
from core.models import Entity
from core.models.mixin import ModelWithFile
from core.models.image import ResizedImageMixin
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import pre_save, pre_delete, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.files.base import ContentFile

from core.utils.convert import tiptap_to_text
from core.utils.access import get_read_access_weight, get_write_access_weight
from file.validators import is_upload_complete

logger = logging.getLogger(__name__)


def read_access_default():
    return []


def write_access_default():
    return []


class FILE_SCAN(Enum):
    CLEAN = 'CLEAN'
    VIRUS = 'VIRUS'
    UNKNOWN = 'UNKNOWN'


class FileFolder(Entity, ModelWithFile, ResizedImageMixin):
    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True, max_length=512)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)
    size = models.IntegerField(default=0)

    last_scan = models.DateTimeField(default=None, null=True)

    read_access_weight = models.IntegerField(default=0)
    write_access_weight = models.IntegerField(default=0)

    rich_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"FileFolder[{self.title}]"

    def make_copy(self, user):
        new = FileFolder()
        new_file = ContentFile(self.upload.read())
        new_file.name = self.upload.name
        new.upload = new_file
        new.owner = user

        new.save()

        return new

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
            else:  # personal file browser url
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

    @property
    def file_fields(self):
        return [self.thumbnail, self.upload]

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def scan(self) -> FILE_SCAN:
        if settings.CLAMAV_HOST:
            cd = clamd.ClamdNetworkSocket(host=settings.CLAMAV_HOST, timeout=120)
            result = None

            try:
                if not os.path.exists(self.upload.path):
                    return FILE_SCAN.CLEAN

                result = cd.instream(self.upload.file)
            except Exception as e:
                logger.error('Clamav error scanning file (%s): %s', self.guid, e)
                return FILE_SCAN.UNKNOWN

            self.last_scan = timezone.now()

            if result and result['stream'][0] == 'FOUND':
                message = result['stream'][1]

                logger.error('Clamav found suspicious file: %s', message)

                ScanIncident.objects.create(
                    message=message,
                    file=self if not self._state.adding else None,
                    file_created=self.created_at,
                    file_title=self.upload.file.name,
                    file_mime_type=get_mimetype(self.upload.path),
                    file_owner=self.owner,
                    file_group=self.group,
                )

                return FILE_SCAN.VIRUS

            return FILE_SCAN.CLEAN

        return FILE_SCAN.UNKNOWN

    @property
    def upload_field(self):
        return self.upload

    @property
    def mime_type_field(self):
        return self.mime_type

    @property
    def description(self):
        return tiptap_to_text(self.rich_description)


class ScanIncident(models.Model):
    date = models.DateTimeField(default=timezone.now)
    message = models.CharField(max_length=256)
    file = models.ForeignKey('file.FileFolder', blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='scan_incidents')
    file_created = models.DateTimeField(default=timezone.now)
    file_group = models.ForeignKey('core.Group', blank=True, null=True, on_delete=models.SET_NULL)
    file_title = models.CharField(max_length=256)
    file_mime_type = models.CharField(null=True, blank=True, max_length=100)
    file_owner = models.ForeignKey('user.User', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-date',)


def set_parent_folders_updated_at(instance):
    if instance == instance.parent:
        return
    if instance.parent and instance.parent.is_folder:
        with signal_disabler.disable():
            instance.parent.save()
        set_parent_folders_updated_at(instance.parent)


@receiver(pre_save, sender=FileFolder)
def file_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    instance.read_access_weight = get_read_access_weight(instance)
    instance.write_access_weight = get_write_access_weight(instance)

    if instance.upload:
        try:
            if not instance.title:
                instance.title = get_basename(instance.upload.path)
            if not instance.mime_type:
                instance.mime_type=get_mimetype(instance.upload.path)
            if not instance.size:
                instance.size=get_filesize(instance.upload.path)
        except FileNotFoundError as e:
            pass


@receiver(post_save, sender=FileFolder)
def file_post_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if not is_upload_complete(instance):
        from file.tasks import post_process_file_attributes
        post_process_file_attributes.delay(tenant_schema(), str(instance.id))


# update parent folders updated_at when adding, moving and deleting files
@receiver([pre_save], sender=FileFolder)
def update_parent_timestamps(sender, instance, **kwargs):
    # pylint: disable=unused-argument

    set_parent_folders_updated_at(instance)

    try:
        # Also update old parent if changed
        old_instance = FileFolder.objects.get(id=instance.id)
        if old_instance.parent != instance.parent:
            set_parent_folders_updated_at(old_instance)
    except ObjectDoesNotExist:
        pass


@receiver(pre_delete, sender=FileFolder)
def cleanup_extra_file(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if instance.is_folder:
        return

    try:
        os.unlink(f"{os.path.dirname(instance.upload.path)}/{instance.title}")
    except (FileNotFoundError, ValueError):
        pass


auditlog.register(FileFolder)
