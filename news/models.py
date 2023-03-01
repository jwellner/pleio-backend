from auditlog.registry import auditlog
from django.db import models

from core.constances import USER_ROLES
from core.lib import get_acl
from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin,
                         CommentMixin, Entity, FollowMixin, MentionMixin,
                         VoteMixin, RevisionMixin)
from core.models.featured import FeaturedCoverMixin
from core.models.mixin import TitleMixin, RichDescriptionMediaMixin


class News(RichDescriptionMediaMixin, TitleMixin, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin,
           FeaturedCoverMixin, ArticleMixin, MentionMixin, AttachmentMixin,
           RevisionMixin, Entity):
    """
    News
    """

    class Meta:
        ordering = ['-published']

    source = models.TextField(default="")

    def has_revisions(self):
        return True

    def __str__(self):
        return f"News[{self.title}]"

    @property
    def type_to_string(self):
        return 'news'

    @property
    def url(self):
        return '/news/view/{}/{}'.format(
            self.guid, self.slug
        ).lower()

    def can_write(self, user):
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

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
            'source': self.source or '',
            'featured': self.serialize_featured(),
            **super().serialize()
        }


auditlog.register(News)
