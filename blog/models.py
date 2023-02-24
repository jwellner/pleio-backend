from auditlog.registry import auditlog
from django.utils.text import slugify

from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin,
                         CommentMixin, Entity, FollowMixin, MentionMixin,
                         VoteMixin, RevisionMixin)
from core.models.featured import FeaturedCoverMixin
from core.models.mixin import TitleMixin, RichDescriptionMediaMixin


class Blog(RichDescriptionMediaMixin, TitleMixin, FeaturedCoverMixin, VoteMixin, BookmarkMixin, FollowMixin,
           CommentMixin, MentionMixin, AttachmentMixin, ArticleMixin, RevisionMixin, Entity):
    """
    Blog
    """

    class Meta:
        ordering = ['-published']

    def __str__(self):
        return f"Blog[{self.title}]"

    def has_revisions(self):
        return True

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
            prefix, self.guid, self.slug
        ).lower()

    @property
    def rich_fields(self):
        return [self.rich_description]

    def map_rich_text_fields(self, callback):
        self.rich_description = callback(self.rich_description)
        self.abstract = callback(self.abstract)

    def serialize(self):
        return {
            'title': self.title or '',
            'richDescription': self.rich_description or '',
            'abstract': self.abstract or '',
            'featured': self.serialize_featured(),
            **super().serialize(),
        }


auditlog.register(Blog)
