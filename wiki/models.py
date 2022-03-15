from auditlog.registry import auditlog
from django.db import models
from core.models import Entity, BookmarkMixin, FeaturedCoverMixin, ArticleMixin, MentionMixin, AttachmentMixin
from django.utils.text import slugify

class Wiki(Entity, FeaturedCoverMixin, BookmarkMixin, ArticleMixin, MentionMixin, AttachmentMixin):
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


auditlog.register(Wiki)
