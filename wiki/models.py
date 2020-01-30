from django.db import models
from core.models import Entity, BookmarkMixin
from django.utils.text import slugify

class Wiki(Entity, BookmarkMixin):
    """
    Wiki
    """
    class Meta:
        ordering = ['position', '-created_at']

    position = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def __str__(self):
        return self.title

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
