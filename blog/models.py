from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import Object, Comment, FileFolder

class Blog(Object):
    """
    TODO: Implement
        - comments
        - votes
        - likes
        
    """
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    is_recommended = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.CharField(max_length=256, null=True, blank=True)
    featured_position_y = models.IntegerField(default=0, null=False)

    comments = GenericRelation(Comment)

    def __str__(self):
        return self.title

    def is_closed(self):
        return False

    def can_comment(self, user):
        if self.is_closed():
            return False

        if not user.is_authenticated:
            return False

        return True

    def can_vote(self, user):
        if self.is_closed():
            return False

        if not user.is_authenticated:
            return False

        return True

    def can_bookmark(self, user):
        if not user.is_authenticated:
            return False

        return True
