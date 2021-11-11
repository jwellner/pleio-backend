from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin


class Discussion(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, NotificationMixin, FeaturedCoverMixin):
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    description = models.TextField(default="")
    rich_description = models.TextField(null=True, blank=True)

    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"Discussion[{self.title}]"

    @property
    def type_to_string(self):
        return 'discussion'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/discussion/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()


auditlog.register(Discussion)