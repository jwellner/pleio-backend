import uuid
from django.db import models
from django.utils import timezone
from core.models import Entity


class Revision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    object = models.ForeignKey(Entity, on_delete=models.CASCADE)

    description = models.TextField(null=True, blank=True)
    content = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
