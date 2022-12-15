from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, MentionMixin, ArticleMixin, AttachmentMixin
from core.models.featured import FeaturedCoverMixin
from core.models.mixin import TitleMixin, RichDescriptionMediaMixin


class Discussion(RichDescriptionMediaMixin, TitleMixin, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, MentionMixin, FeaturedCoverMixin, ArticleMixin, AttachmentMixin, Entity):
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)

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
            prefix, self.guid, self.slug
        ).lower()

    @property
    def rich_fields(self):
        return [self.rich_description]


auditlog.register(Discussion)
