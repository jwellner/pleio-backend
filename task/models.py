from django.db import models
from core.models import Entity
from django.utils.text import slugify

class Task(Entity):
    """
    Task
    """
    class Meta:
        ordering = ['-created_at']

    STATE_TYPES = (
        ('NEW', 'New'),
        ('BUSY', 'Busy'),
        ('DONE', 'Done')
    )

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    state = models.CharField(
        max_length=32,
        choices=STATE_TYPES,
        default='NEW'
    )

    def __str__(self):
        return self.title

    @property
    def type_to_string(self):
        return 'task'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/task/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()
