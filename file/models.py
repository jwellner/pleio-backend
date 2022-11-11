import os
import clamd
import logging

from auditlog.registry import auditlog
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.utils import timezone
from enum import Enum
from core.constances import DOWNLOAD_AS_OPTIONS
from core.lib import generate_object_filename, get_mimetype, tenant_schema, get_basename, get_filesize
from core.models import Entity
from core.models.entity import EntityManager
from core.models.mixin import ModelWithFile
from core.models.rich_fields import AttachmentMixin
from core.models.image import ResizedImageMixin
from django.db.models import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile

from core.utils.convert import tiptap_to_text
from core.utils.access import get_read_access_weight, get_write_access_weight
from file.validators import is_upload_complete

logger = logging.getLogger(__name__)


def read_access_default():
    return []


def write_access_default():
    return []


class FILE_SCAN(str, Enum):
    CLEAN = 'CLEAN'
    VIRUS = 'VIRUS'
    UNKNOWN = 'UNKNOWN'


class FileFolderManager(EntityManager):

    def file_by_path(self, path):
        for maybe_guid in path.split('/'):
            try:
                qs = self.get_queryset().filter(pk=maybe_guid, type=FileFolder.Types.FILE)
                if qs.exists():
                    return qs.first()
            except Exception:
                pass
        return None


class FileFolder(Entity, ModelWithFile, ResizedImageMixin, AttachmentMixin):
    class Types(models.TextChoices):
        FILE = "File", _("File")
        FOLDER = "Folder", _("Folder")
        PAD = "Pad", _("Pad")

    objects = FileFolderManager()

    title = models.CharField(max_length=256)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    type = models.CharField(
        max_length=36,
        choices=Types.choices,
        default=Types.FILE
    )

    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True, max_length=512)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)
    size = models.IntegerField(default=0)

    last_scan = models.DateTimeField(default=None, null=True)
    last_download = models.DateTimeField(default=None, null=True)

    read_access_weight = models.IntegerField(default=0)
    write_access_weight = models.IntegerField(default=0)

    rich_description = models.TextField(null=True, blank=True)
    pad_state = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"FileFolder[{self.title}]"

    @property
    def type_to_string(self):
        return self.type.lower()

    @property
    def url(self):
        prefix = ''

        if self.type == self.Types.FOLDER:
            if self.group:
                prefix = '/groups/view/{}/{}'.format(
                    self.group.guid, slugify(self.group.name)
                )
            else:  # personal file browser url
                prefix = '/user/{}'.format(self.owner.guid)

            return '{}/files/{}'.format(
                prefix, self.guid
            ).lower()

        if self.type == self.Types.FILE:
            return '{}/files/view/{}/{}'.format(
                prefix, self.guid, os.path.basename(self.upload.name)
            ).lower()

        return '{}/files/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()

    @property
    def download_url(self):
        if self.type != self.Types.FILE:
            return None
        return reverse('download', args=[self.id, os.path.basename(self.upload.name)])

    @property
    def embed_url(self):
        if self.type != self.Types.FILE:
            return None
        return reverse('embed', args=[self.id, os.path.basename(self.upload.name)])

    @property
    def thumbnail_url(self):
        if self.type != self.Types.FILE:
            return None
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

    @property
    def rich_fields(self):
        return [self.rich_description]

    @property
    def download_as_options(self):
        if self.type != self.Types.PAD:
            return None
        download_as_options = []
        for option in DOWNLOAD_AS_OPTIONS:
            download_as_options.append({"type": option, "url": "/download_rich_description_as/{}/{}".format(self.guid, option) })
        return download_as_options

    def save(self, *args, **kwargs):
        self.update_metadata()
        super(FileFolder, self).save(*args, **kwargs)
        if not is_upload_complete(self):
            from file.tasks import post_process_file_attributes
            post_process_file_attributes.delay(tenant_schema(), str(self.id))

    def delete(self, *args, **kwargs):
        self.cleanup_extra_file()
        super(FileFolder, self).delete(*args, **kwargs)

    def update_metadata(self):
        self.read_access_weight = get_read_access_weight(self)
        self.write_access_weight = get_write_access_weight(self)
        if self.upload:
            try:
                if not self.title:
                    self.title = get_basename(self.upload.name)
                self.mime_type = get_mimetype(self.upload.path)
                self.size = self.upload.size
            except FileNotFoundError:
                pass

    def update_updated_at(self):
        """ Needs to be executed before save so we can compare if the File or Folder moved to a new parent and also update those dates"""
        self.updated_at = timezone.now()
        set_parent_folders_updated_at(self)

        try:
            # Also update old parent if changed
            old_instance = FileFolder.objects.get(id=self.id)
            if old_instance.parent != self.parent:
                set_parent_folders_updated_at(old_instance)
        except ObjectDoesNotExist:
            pass

    def cleanup_extra_file(self):
        # pylint: disable=unused-argument
        if not self.type == FileFolder.Types.FILE:
            return

        try:
            os.unlink(f"{os.path.dirname(self.upload.path)}/{self.title}")
        except (FileNotFoundError, ValueError):
            pass

    def get_content(self, wrap=None):
        if os.path.exists(self.upload.path):
            with open(self.upload.path, 'rb') as fh:
                data = fh.read()
                if callable(wrap):
                    return wrap(data)
                return data
        return None

    def make_copy(self, user):
        new = FileFolder()
        new_file = ContentFile(self.upload.read())
        new_file.name = self.upload.name
        new.upload = new_file
        new.owner = user

        new.save()

        return new


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
    if instance.parent and instance.parent.type == FileFolder.Types.FOLDER:
        instance.parent.updated_at = timezone.now()
        instance.parent.save()
        set_parent_folders_updated_at(instance.parent)


auditlog.register(FileFolder)
