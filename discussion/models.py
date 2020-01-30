from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin


class Discussion(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin):
    class Meta:
        ordering = ['-created_at']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

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
