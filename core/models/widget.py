
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


class Widget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        'core.Group',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    settings = ArrayField(JSONField(help_text="Please provide valid JSON data"), blank=True, default=list)
    position = models.IntegerField(null=False)
    type = models.CharField(max_length=64)
    parent_id = models.UUIDField(default=uuid.uuid4)

    @property
    def guid(self):
        return str(self.id)

    def can_write(self, user):
        if user.is_authenticated and user.is_admin:
            return True

        return self.group.can_write(user)
