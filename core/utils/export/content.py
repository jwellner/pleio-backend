import logging
import os
import zipfile
from io import BytesIO

from django.utils import timezone

from core.models import Entity, Attachment
from core.models.mixin import HasMediaMixin

logger = logging.getLogger(__name__)


class ContentSnapshot:
    EXCLUDE_TAG = 'exclude-from-content-export'

    def __init__(self, user_guid):
        from user.models import User
        self.user = User.objects.get(id=user_guid)

    def collect_content(self):
        buffer = BytesIO()
        zip_file = zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED)
        query = Entity.objects.filter(owner=self.user.guid)

        for entity in query.select_subclasses():
            folder = self.folder_name(entity)
            if isinstance(entity, HasMediaMixin) and entity.get_media_status() and self.EXCLUDE_TAG not in entity.tags:
                zip_file.writestr(
                    os.path.join(folder, entity.get_media_filename()),
                    entity.get_media_content(),
                )
            for attachment in Attachment.objects.filter_attached(entity):
                if attachment.get_media_status():
                    zip_file.writestr(
                        os.path.join(folder, attachment.get_media_filename()),
                        attachment.get_media_content()
                    )
        zip_file.close()
        buffer.seek(0)
        return buffer.read()

    def folder_name(self, entity):
        created = entity.created_at.astimezone(timezone.get_current_timezone())
        return os.path.join(
            entity._meta.label,
            created.strftime("%Y"),
            created.strftime("%m"),
            created.strftime("%d"),
            created.strftime("%H.%M.%S")
        )
