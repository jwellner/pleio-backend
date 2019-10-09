from django.db import models
from core.models import Entity, FileFolder, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin

class News(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin):
    """
    News
    """
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    
    is_featured = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.CharField(max_length=256, null=True, blank=True)
    featured_position_y = models.IntegerField(default=0, null=False)

    source = models.CharField(max_length=256, default="")

    def __str__(self):
        return self.title
