from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin
from file.models import FileFolder
from django.urls import reverse

class Blog(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, NotificationMixin):
    """
    Blog
    """
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)
    is_recommended = models.BooleanField(default=False)

    is_featured = models.BooleanField(default=False)

    featured_image = models.ForeignKey(
        FileFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    featured_video = models.TextField(null=True, blank=True)
    featured_video_title = models.CharField(max_length=256, default="")
    featured_position_y = models.IntegerField(default=0, null=False)
    featured_alt = models.CharField(max_length=256, default="")

    def __str__(self):
        return f"Blog[{self.title}]"

    @property
    def type_to_string(self):
        return 'blog'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/blog/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()

    @property
    def featured_image_url(self):
        if self.featured_image:
            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(self.featured_image.updated_at.timestamp()))
        return None


auditlog.register(Blog)