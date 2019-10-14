from django.db import models
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin

class StatusUpdate(Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin):
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

    def type_to_string(self):
        return 'thewire'
