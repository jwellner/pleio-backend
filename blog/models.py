from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import Object, Comment, FileFolder


class Blog(Object):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()
    comments = GenericRelation(Comment)

    is_featured = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.CharField(max_length=256, null=True, blank=True)
    featured_position_y = models.IntegerField(default=0, null=False)

    def __str__(self):
        return self.title

    def can_comment(self, user):
        if not user.is_authenticated:
            return False

        return True
