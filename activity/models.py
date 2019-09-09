from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import Entity, Comment

class StatusUpdate(Entity):
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    comments = GenericRelation(Comment)

    def __str__(self):
        return self.title

    def can_comment(self, user):
        if not user.is_authenticated:
            return False

        return True
