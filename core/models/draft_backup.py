
import uuid
from django.db import models


class DraftBackup(models.Model):
    """
    Used to store original draftjs data before conversion as backup
    """
    content_id = models.UUIDField(default=uuid.uuid4)
    property = models.CharField(max_length=36)
    data = models.JSONField()
    is_html = models.BooleanField(default=False)

    class Meta:
        unique_together = ('content_id', 'property')
