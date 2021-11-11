from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, FeaturedCoverMixin
from core.constances import USER_ROLES
from core.lib import get_acl


class News(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, FeaturedCoverMixin):
    """
    News
    """
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    description = models.TextField(default="")
    rich_description = models.TextField(null=True, blank=True)

    is_featured = models.BooleanField(default=False)

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


auditlog.register(News)