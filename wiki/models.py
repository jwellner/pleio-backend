from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify

from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin, Entity,
                         MentionMixin, RevisionMixin)
from core.models.featured import FeaturedCoverMixin
from core.models.mixin import TitleMixin, RichDescriptionMediaMixin


class Wiki(RichDescriptionMediaMixin, TitleMixin, FeaturedCoverMixin, BookmarkMixin, ArticleMixin, MentionMixin,
           AttachmentMixin, RevisionMixin, Entity):
    """
    Wiki
    """

    class Meta:
        # When positions are equal sort old -> new (used for menu's)
        ordering = ['position', 'published']

    position = models.IntegerField(null=False, default=0)
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
            'containerGuid': self.parent.guid if self.parent else None,
            **super().serialize(),
        }


auditlog.register(Wiki)
