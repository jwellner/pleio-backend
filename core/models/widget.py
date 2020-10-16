
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Widget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        'core.Group',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    settings = ArrayField(models.JSONField(help_text="Please provide valid JSON data"), blank=True, default=list)
    position = models.IntegerField(null=False)
    type = models.CharField(max_length=64)
    page = models.ForeignKey(
        'cms.Page',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    column = models.ForeignKey(
        'cms.Column',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='widgets'
    )
    @property
    def guid(self):
        return str(self.id)

    def can_write(self, user):
        if self.group:
            return self.group.can_write(user)

        if self.page:
            return self.page.can_write(user)

        return False

    @property
    def type_to_string(self):
        return 'widget'
