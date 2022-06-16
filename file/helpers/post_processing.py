import logging

from core.lib import get_basename, get_mimetype, get_filesize, tenant_schema
from file.models import FileFolder
from file.validators import valid_filename, valid_mimetype, valid_filesize

logger = logging.getLogger(__name__)


def ensure_correct_file_without_signals(instance):
    try:
        if instance.upload:
            if not valid_filename(instance.title):
                FileFolder.objects.filter(id=instance.id).update(title=get_basename(instance.upload.path))
            if not valid_mimetype(instance.mime_type):
                FileFolder.objects.filter(id=instance.id).update(mime_type=get_mimetype(instance.upload.path))
            if not valid_filesize(instance.size):
                FileFolder.objects.filter(id=instance.id).update(size=get_filesize(instance.upload.path))
            instance.refresh_from_db()
    except Exception as e:
        logger.error("update_instance_without_signals error: %s %s for %s@%s", e.__class__, e, instance.id, tenant_schema())
