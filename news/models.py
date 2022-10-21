from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, ArticleMixin, MentionMixin, AttachmentMixin
from core.constances import USER_ROLES
from core.lib import get_acl, get_access_id
from core.models.entity import str_datetime
from core.models.featured import FeaturedCoverMixin


class News(Entity, VoteMixin, BookmarkMixin, FollowMixin, CommentMixin, FeaturedCoverMixin, ArticleMixin, MentionMixin, AttachmentMixin):
    """
    News
    """

    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
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
            self.guid, slugify(self.title)
        ).lower()

    def can_write(self, user):
        if user.is_authenticated and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def rich_fields(self):
        return [self.rich_description]

    def serialize(self):
        return {
            'title': self.title or '',
            'richDescription': self.rich_description or '',
            'accessId': get_access_id(self.read_access),
            'writeAccessId': get_access_id(self.write_access),
            'tags': sorted(self.tags) or [],
            'tagCategories': self.category_tags or [],
            'timeCreated': str_datetime(self.created_at),
            'timePublished': str_datetime(self.published),
            'scheduleArchiveEntity': str_datetime(self.schedule_archive_after),
            'scheduleDeleteEntity': str_datetime(self.schedule_delete_after),
            'abstract': self.abstract or '',
            'source': self.source or '',
            'isFeatured': bool(self.is_featured),
            'featured': self.serialize_featured(),
            'ownerGuid': self.owner.guid if self.owner else None,
            'suggestedItems': [str(item) for item in self.suggested_items or []],
        }


auditlog.register(News)
