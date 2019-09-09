from django.db import models
from core.models import Entity


class Event(Entity):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.title
