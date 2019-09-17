
from django.db import models
from django.contrib.postgres.fields import JSONField


class Setting(models.Model):
    key = models.CharField(max_length=255)
    value = JSONField(null=True, blank=True, help_text="Please provide valid JSON data")

    def __str__(self):
        return self.key
