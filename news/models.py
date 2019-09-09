from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from core.models import Object, FileFolder, Comment

class News(Object):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()

    is_featured = models.BooleanField(default=False)

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
    def views(self):
        return 0
