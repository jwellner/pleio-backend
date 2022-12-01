from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify

from core.lib import get_access_id
from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin, Entity,
                         MentionMixin, RevisionMixin)
from core.models.entity import str_datetime
from core.models.featured import FeaturedCoverMixin


class Wiki(Entity, FeaturedCoverMixin, BookmarkMixin, ArticleMixin, MentionMixin, 
           AttachmentMixin, RevisionMixin):
    """
    Wiki
    """

    class Meta:
        # When positions are equal sort old -> new (used for menu's)
        ordering = ['position', 'published']

    position = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=256)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def has_revisions(self):
        return True
    
    def __str__(self):
        return f"Wiki[{self.title}]"

    @property
    def type_to_string(self):
        return 'wiki'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/wiki/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
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
            'isFeatured': bool(self.is_featured),
            'featured': self.serialize_featured(),
            'groupGuid': self.group.guid if self.group else None,
            'ownerGuid': self.owner.guid if self.owner else None,
            'containerGuid': self.parent.guid if self.parent else None,
        }



auditlog.register(Wiki)
