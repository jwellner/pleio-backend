from django.db import models
from backend.core.models import Object

class Blog(Object):
    title = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.title