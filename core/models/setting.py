
from auditlog.registry import auditlog
from django.db import models


class Setting(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(null=True, blank=True, help_text="Please provide valid JSON data")

    def __str__(self):
        return f"Setting[{self.key}]"


auditlog.register(Setting)