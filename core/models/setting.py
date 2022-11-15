from auditlog.registry import auditlog
from django.db import models


class SettingManager(models.Manager):
    # Separate manager allows testing specific aspects of the model.
    pass


class Setting(models.Model):
    objects = SettingManager()

    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(null=True, blank=True, help_text="Please provide valid JSON data")

    def __str__(self):
        return f"Setting[{self.key}]"


auditlog.register(Setting)
