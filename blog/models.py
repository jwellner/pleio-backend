from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin

class Blog(Entity, FeaturedCoverMixin, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, NotificationMixin):
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


auditlog.register(Blog)