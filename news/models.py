from django.db import models
from core.models import Object


class News(Object):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()

    @property
    def comments(self):
        return []

    @property
    def votes(self):
        return 0

    @property
    def has_voted(self):
        return False

    @property
    def is_bookmarked(self):
        return False

    @property
    def is_following(self):
        return False

    @property
    def can_bookmark(self):
        return False

    @property
    def is_featured(self):
        return False

    @property
    def views(self):
        return 0

    def __str__(self):
        return self.title
