from django.db import models
from core.models import Entity
from core.models import BookmarkMixin

class Wiki(Entity, BookmarkMixin):
    """
    Wiki
    """
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def __str__(self):
        return self.title
