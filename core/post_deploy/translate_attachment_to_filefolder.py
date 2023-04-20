import json
import os
import re
import uuid

from celery import shared_task, chord
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone
from django_tenants.utils import schema_context
from post_deploy import post_deploy_action

from blog.models import Blog
from core import config
from core.constances import ACCESS_TYPE, CONFIGURED_LOGO_FILE, CONFIGURED_ICON_FILE, CONFIGURED_FAVICON_FILE
from core.lib import is_schema_public, tenant_schema
from core.models import Attachment, Group, Revision, Entity
from discussion.models import Discussion
from event.models import Event
from file.models import FileFolder, FileReference
from question.models import Question
from wiki.models import Wiki

logger = get_task_logger(__name__)


def migrate_revision(revision):
    def is_uuid(maybe_uuid):
        try:
            uuid.UUID(maybe_uuid)
            return True
        except ValueError:
            return False

    maybe_attachments = [*re.findall(r"[0-9a-f\-]{36}", json.dumps(revision.serialize_previous_version()))]
    maybe_attachments = [*filter(is_uuid, maybe_attachments)]

    native_attachments = [str(id) for id in Attachment.objects.filter(id__in=maybe_attachments).values_list('id', flat=True)]
    file_attachments = [str(id) for id in FileFolder.objects.filter(id__in=maybe_attachments).values_list('id', flat=True)]

    revision.attachments = [*file_attachments, *native_attachments]
    revision.save()


def process_revisions():
    for revision in Revision.objects.all():
        migrate_revision(revision)


@shared_task
def migrate_attachment(schema_name, attachment_id):
    # Create a filefolder with the same guid
    with schema_context(schema_name):
        attachment = None
        try:
            attachment = Attachment.objects.get(pk=attachment_id)
            assert os.path.exists(attachment.upload.path), "Attachment does not exist"

            file, _ = FileFolder.objects.get_or_create(
                id=attachment.id,
                type=FileFolder.Types.FILE,
                owner=attachment.owner,
            )
            file.title = os.path.basename(attachment.upload.name)
            file.created_at = attachment.created_at
            file.updated_at = timezone.now()
            file.upload = attachment.upload
            file.write_access = [ACCESS_TYPE.user.format(file.owner)]
            file.save()

            if file.resized_images.get_queryset().count() == 0:
                for image in attachment.resized_images.get_queryset():
                    image.original = file
                    image.save()

            container = _maybe_entity_object(attachment.attached_object_id)
            if container:
                # Create File Reference.
                reference, _ = FileReference.objects.get_or_create(file=file, container=container)
                FileReference.objects.filter(pk=reference.pk).update(created_at=attachment.created_at)

            # Remove the attachment, but not the file on the disk.
            Attachment.objects.filter(pk=attachment_id).update(upload=None)
            attachment.refresh_from_db()
            attachment.delete()

            return file.guid
        except Exception as e:
            if attachment:
                logger.error("migrate_attachment error: %s %s@%s %s %s", tenant_schema(), attachment.name, attachment.attached_object_id, e.__class__, str(e))
            else:
                logger.error("migrate_attachment error: %s %s@%s %s %s", tenant_schema(), attachment_id, '???', e.__class__, str(e))


def _maybe_entity_object(entity_id):
    return Entity.objects.filter(pk=entity_id).select_subclasses().first()


def persist_files_from_settings():
    def update_configuration(key, value):
        if not value:
            return
        file = FileFolder.objects.file_by_path(value)
        if not file:
            return
        FileReference.objects.update_configuration(key, [file.id])

    update_configuration(CONFIGURED_LOGO_FILE, config.LOGO)
    update_configuration(CONFIGURED_ICON_FILE, config.ICON)
    update_configuration(CONFIGURED_FAVICON_FILE, config.FAVICON)


def persist_group_icons():
    for group in Group.objects.filter(Q(icon__isnull=False) | Q(featured_image__isnull=False)):
        try:
            if group.icon:
                FileReference.objects.get_or_create(container=group, file_id=group.icon_id)
            if group.featured_image:
                FileReference.objects.get_or_create(container=group, file_id=group.featured_image_id)
        except Exception as e:
            pass


def persist_featured_media():
    def _persist_featured_image(qs):
        for entity in qs:
            FileReference.objects.get_or_create(container=entity, file_id=entity.featured_image_id)

    _persist_featured_image(Blog.objects.filter(featured_image__isnull=False))
    _persist_featured_image(Discussion.objects.filter(featured_image__isnull=False))
    _persist_featured_image(Event.objects.filter(featured_image__isnull=False))
    _persist_featured_image(Question.objects.filter(featured_image__isnull=False))
    _persist_featured_image(Wiki.objects.filter(featured_image__isnull=False))


def persist_other_files():
    # mark all files as persistent that not yet are in groups or attached.
    for file in FileFolder.objects.filter_orphaned_files():
        file.persist_file()


def process_attachments():
    attachment_ids = [str(pk) for pk in Attachment.objects.all().values_list('id', flat=True)]
    for attachment in attachment_ids:
        yield migrate_attachment.si(tenant_schema(), attachment)


@shared_task
def schedule_calculate_checksum(schema_name):
    with schema_context(schema_name):
        from core.tasks.misc import update_file_checksum
        for file in FileFolder.objects.filter_attachments():
            if file.is_image():
                update_file_checksum.delay(tenant_schema(), file.guid)


@post_deploy_action(auto=True)
def task():
    """
    Niet tegelijk met add_attachments_to_revision laten lopen.
    """
    if is_schema_public():
        return

    process_revisions()
    chord([*process_attachments()], schedule_calculate_checksum.si(tenant_schema())).apply_async()

    persist_files_from_settings()
    persist_group_icons()
    persist_featured_media()
    persist_other_files()
