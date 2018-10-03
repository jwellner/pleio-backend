from django.db import models
from core.models import Object


class News(Object):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
