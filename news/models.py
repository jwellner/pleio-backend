from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, FeaturedCoverMixin, ArticleMixin, MentionMixin, AttachmentMixin
from core.constances import USER_ROLES
from core.lib import get_acl


class News(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, FeaturedCoverMixin, ArticleMixin, MentionMixin, AttachmentMixin):
    """
    News
    """
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    source = models.TextField(default="")

    def __str__(self):
        return f"News[{self.title}]"

    @property
    def type_to_string(self):
        return 'news'

    @property
    def url(self):
        return '/news/view/{}/{}'.format(
            self.guid, slugify(self.title)
        ).lower()

    def can_write(self, user):
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def rich_fields(self):
        return [self.rich_description]


auditlog.register(News)
