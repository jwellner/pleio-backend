from auditlog.registry import auditlog
from django.utils.text import slugify

from core.lib import get_access_id
from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin,
                         CommentMixin, Entity, FollowMixin, MentionMixin,
                         VoteMixin, RevisionMixin)
from core.models.entity import str_datetime
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
            'statusPublished': self.status_published,
            'scheduleArchiveEntity': str_datetime(self.schedule_archive_after),
            'scheduleDeleteEntity': str_datetime(self.schedule_delete_after),
            'abstract': self.abstract or '',
            'isRecommended': bool(self.is_recommended),
            'isFeatured': bool(self.is_featured),
            'featured': self.serialize_featured(),
            'groupGuid': self.group.guid if self.group else None,
            'ownerGuid': self.owner.guid if self.owner else None,
            'suggestedItems': [str(item) for item in self.suggested_items or []],
        }


auditlog.register(Blog)
