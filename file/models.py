import logging
import os
from hashlib import md5

from auditlog.registry import auditlog
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.db import models
from django.utils import timezone
from model_utils.managers import InheritanceQuerySet

from core.constances import DOWNLOAD_AS_OPTIONS, ACCESS_TYPE, PERSONAL_FILE
from core.lib import generate_object_filename, get_mimetype, tenant_schema, get_basename, get_file_checksum
from core.models import Entity, Tag
from core.models.entity import EntityManager
from core.models.mixin import ModelWithFile, TitleMixin, HasMediaMixin
from core.models.rich_fields import AttachmentMixin
from core.models.image import ResizedImageMixin
from django.db.models import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile

from core.models.tags import EntityTag
from core.utils import clamav
from core.utils.convert import tiptap_to_text, tiptap_to_html
from core.utils.access import get_read_access_weight, get_write_access_weight
from core.utils.export.content import ContentSnapshot
from file.validators import is_upload_complete

logger = logging.getLogger(__name__)


def read_access_default():
    return []


def write_access_default():
    return []


class FileReferenceQuerySet(models.QuerySet):

    def exclude_personal_references(self):
        return self.exclude(configuration=PERSONAL_FILE)


class FileReferenceManager(models.Manager):

    def get_queryset(self):
        return FileReferenceQuerySet(self.model, using=self._db)

    def persist_file(self, file):
        super().get_or_create(file=file,
                              container_ct=None,
                              container_fk=None,
                              configuration=PERSONAL_FILE)

    def update_configuration(self, configuration, file_ids):
        qs = self.get_queryset().filter(configuration=configuration)
        if file_ids:
            qs = qs.exclude(file_id__in=file_ids)
        qs.delete()

        if file_ids:
            for guid in file_ids:
                super().get_or_create(configuration=configuration,
                                      file_id=guid)

    def get_or_create(self, container, **kwargs):
        try:
            return self.get(container_fk=container.id, **kwargs), False
        except FileReference.DoesNotExist:
            return self.create(container=container,
                               **kwargs), True

    def exclude_personal_references(self):
        return self.get_queryset().exclude_personal_references()


class FileReference(models.Model):
    objects = FileReferenceManager()

    created_at = models.DateTimeField(default=timezone.now)

    file = models.ForeignKey('file.FileFolder',
                             blank=False,
                             null=False,
                             on_delete=models.CASCADE,
                             related_name='referenced_by')
    container_ct = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    container_fk = models.UUIDField(blank=True, null=True)
    container = GenericForeignKey(ct_field='container_ct', fk_field='container_fk')

    configuration = models.CharField(max_length=256, blank=True, null=True)

    def delete(self, using=None, keep_parents=False):
        file = self.file
        super().delete(using=using, keep_parents=keep_parents)

        if file.refresh_read_access():
            file.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file.refresh_read_access():
            self.file.save()


class FileFolderQuerySet(InheritanceQuerySet):

    def filter_files(self):
        return self.filter(type=FileFolder.Types.FILE)

    def filter_orphaned_files(self):
        qs = self.filter_files()
        return qs.filter(group__isnull=True,
                         referenced_by__isnull=True)

    def filter_attachments(self):
        qs = self.filter_files()
        return qs.filter(group__isnull=True)


class FileFolderManager(EntityManager):
    def get_queryset(self):
        return FileFolderQuerySet(self.model, using=self._db)

    def file_by_path(self, path):
        for maybe_guid in path.split('/'):
            try:
                qs = self.get_queryset().filter(pk=maybe_guid, type=FileFolder.Types.FILE)
                if qs.exists():
                    return qs.first()
            except Exception:
                pass
        return None

    def content_snapshots(self, user):
        tags = [t for t in Tag.translate_tags([ContentSnapshot.EXCLUDE_TAG])]
        all_snapshots = EntityTag.objects.filter(tag__label__in=tags).values_list('entity_id', flat=True)
        qs = self.visible(user=user)
        qs = qs.filter(owner=user)
        qs = qs.filter(id__in=all_snapshots)
        return qs.order_by('-created_at')

    def filter_files(self):
        return self.get_queryset().filter_files()

    def filter_orphaned_files(self):
        return self.get_queryset().filter_orphaned_files()

    def filter_attachments(self):
        return self.get_queryset().filter_attachments()


class FileFolder(HasMediaMixin, TitleMixin, ModelWithFile, ResizedImageMixin, AttachmentMixin, Entity):
    class Types(models.TextChoices):
        FILE = "File", _("File")
        FOLDER = "Folder", _("Folder")
        PAD = "Pad", _("Pad")

    objects = FileFolderManager()

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    type = models.CharField(
        max_length=36,
        choices=Types.choices,
        default=Types.FILE
    )

    upload = models.FileField(upload_to=generate_object_filename, blank=True, null=True, max_length=512)
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)
    checksum = models.CharField(max_length=32, blank=True, null=True)

    mime_type = models.CharField(null=True, blank=True, max_length=100)
    size = models.IntegerField(default=0)

    last_scan = models.DateTimeField(default=timezone.now)
    last_download = models.DateTimeField(default=None, null=True)

    blocked = models.BooleanField(default=False)
    block_reason = models.CharField(max_length=255, null=True, blank=True)

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

        return '{}/files/view/{}/{}'.format(
            prefix, self.guid, self.slug
        ).lower()

    @property
    def slug(self):
        if self.type == self.Types.FILE:
            return os.path.basename(self.upload.name) or super().slug
        return super().slug

    @property
    def download_url(self):
        if self.type != self.Types.FILE:
            return None
        return reverse('download', args=[self.id, self.slug])

    @property
    def attachment_url(self):
        return reverse('attachment', kwargs={'attachment_id': self.id, 'attachment_type': 'entity'})

    @property
    def embed_url(self):
        if self.type != self.Types.FILE:
            return None
        return reverse('embed', args=[self.id, self.slug])

    @property
    def thumbnail_url(self):
        if self.type != self.Types.FILE:
            return None
        checksum = "?check=%s" % md5(self.upload.name.encode()).hexdigest()[:12] if self.upload.name else ''
        return reverse('thumbnail', args=[self.id]) + checksum

    @property
    def file_fields(self):
        return [self.thumbnail, self.upload]

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

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
            download_as_options.append({"type": option, "url": "/download_rich_description_as/{}/{}".format(self.guid, option)})
        return download_as_options

    def is_referenced(self):
        if self.group:
            return True
        if self.referenced_by.count() > 0:
            return True
        return False

    def refresh_read_access(self):
        if self.group:
            return False
        new_read_access = {ACCESS_TYPE.user.format(self.owner.guid)}
        for referencing in self.referenced_by.all():
            if referencing.configuration:
                new_read_access.add(ACCESS_TYPE.public)
            elif referencing.container:
                for ac in referencing.container.get_read_access():
                    new_read_access.add(ac)

        if new_read_access != {*self.read_access}:
            self.read_access = [*new_read_access]
            return True
        return False

    def get_media_status(self):
        if self.type == self.Types.PAD:
            return bool(self.rich_description)
        if self.type == self.Types.FILE:
            return bool(self.upload.name and os.path.exists(self.upload.path))
        return False

    def get_media_filename(self):
        if self.upload.name and self.upload.path:
            return "%s/%s" % (self.pk, os.path.basename(self.upload.path))
        if self.type == self.Types.PAD:
            return "%s.html" % self.slug
        return None

    def clean_filename(self):
        if not self.upload:
            return self.title
        # Take the extension from the diskfile, and the filename from self.title
        _, ext = os.path.splitext(self.upload.path)
        basename, _ = os.path.splitext(self.title)
        return slugify(basename) + ext.lower()

    def get_media_content(self):
        if self.type == self.Types.FILE and not self.blocked:
            with open(self.upload.path, 'rb') as fh:
                return fh.read()
        if self.type == self.Types.PAD:
            return tiptap_to_html(self.rich_description)
        return None

    def persist_file(self):
        FileReference.objects.persist_file(file=self)

    def save(self, *args, **kwargs):
        self.ensure_owner_read_access()
        self.ensure_owner_write_access()
        self.update_metadata()
        super(FileFolder, self).save(*args, **kwargs)
        if not is_upload_complete(self):
            from file.tasks import post_process_file_attributes
            post_process_file_attributes.delay(tenant_schema(), str(self.id))

    def ensure_owner_read_access(self):
        if not self.read_access:
            self.read_access = [ACCESS_TYPE.user.format(self.owner.guid)]

    def ensure_owner_write_access(self):
        if not self.write_access:
            self.write_access = [ACCESS_TYPE.user.format(self.owner.guid)]

    def scan(self):
        try:
            if self.is_file():
                FileFolder.objects.filter(id=self.id).update(last_scan=timezone.now())
                clamav.scan(self.upload.path)
            return True
        except AttributeError:
            return False
        except clamav.FileScanError as e:
            ScanIncident.objects.create_from_file_folder(e, self)
            return not e.is_virus()

    def delete(self, *args, **kwargs):
        self.cleanup_extra_file()
        super(FileFolder, self).delete(*args, **kwargs)

    def update_metadata(self):
        if self.upload:
            self._update_type_size()
        self._update_title()
        self._update_checksum()
        self.read_access_weight = get_read_access_weight(self)
        self.write_access_weight = get_write_access_weight(self)

    def _update_title(self):
        if not self.title and self.upload:
            self.title = get_basename(self.upload.name)

    def _update_type_size(self):
        try:
            self.mime_type = get_mimetype(self.upload.path)
            self.size = self.upload.size
        except FileNotFoundError:
            pass

    def _update_checksum(self):
        if self.checksum:
            return
        if not self.group and self.is_image():
            self.checksum = get_file_checksum(self.upload)
        else:
            from core.tasks.misc import update_file_checksum
            update_file_checksum.delay(tenant_schema(), self.guid)

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
        if self.type != FileFolder.Types.FILE:
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
        new_file.name = self.clean_filename()
        new.upload = new_file
        new.owner = user
        new.save()

        return new

    def map_rich_text_fields(self, callback):
        self.rich_description = callback(self.rich_description)

    def serialize(self):
        return {
            'title': self.title,
            'file': self.upload.name,
            'mimeType': self.mime_type,
            'size': self.size,
            'richDescription': self.rich_description,
            'parentGuid': str(self.parent_id) if self.parent else None,
            **super().serialize()
        }

    def is_file(self):
        return self.type == self.Types.FILE


class ScanIncidentManager(models.Manager):
    def create_from_attachment(self, e, attachment):
        self.create(message=e.feedback,
                    is_virus=e.is_virus(),
                    file_group=attachment.group,
                    file_created=attachment.created_at,
                    file_title=attachment.upload.name,
                    file_mime_type=get_mimetype(attachment.upload.path),
                    file_owner=attachment.owner)

    def create_from_file_folder(self, e, file_folder):
        self.create(message=e.feedback,
                    is_virus=e.is_virus(),
                    file_group=file_folder.group,
                    file_created=file_folder.created_at,
                    file_title=file_folder.upload.name,
                    file_mime_type=get_mimetype(file_folder.upload.path),
                    file_owner=file_folder.owner)


class ScanIncident(models.Model):
    objects = ScanIncidentManager()

    date = models.DateTimeField(default=timezone.now)
    message = models.CharField(max_length=256)
    file = models.ForeignKey('file.FileFolder', blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='scan_incidents')
    file_created = models.DateTimeField(default=timezone.now)
    file_group = models.ForeignKey('core.Group', blank=True, null=True, on_delete=models.SET_NULL)
    file_title = models.CharField(max_length=256)
    file_mime_type = models.CharField(null=True, blank=True, max_length=100)
    file_owner = models.ForeignKey('user.User', blank=True, null=True, on_delete=models.SET_NULL)
    is_virus = models.BooleanField(default=False)

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
