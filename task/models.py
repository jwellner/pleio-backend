from auditlog.registry import auditlog
from django.db import models
from core.models import Entity, AttachmentMixin
from core.models.mixin import TitleMixin
from core.utils.convert import tiptap_to_text
from django.utils.text import slugify


class Task(TitleMixin, AttachmentMixin, Entity):
    class Meta:
        ordering = ['-published']

    STATE_TYPES = (
        ('NEW', 'New'),
        ('BUSY', 'Busy'),
        ('DONE', 'Done')
    )

    rich_description = models.TextField(null=True, blank=True)

    state = models.CharField(
        max_length=32,
        choices=STATE_TYPES,
        default='NEW'
    )

    def __str__(self):
        return f"Task[{self.title}]"

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
            prefix, self.guid, self.slug
        ).lower()

    @property
    def rich_fields(self):
        return [self.rich_description]

    @property
    def description(self):
        return tiptap_to_text(self.rich_description)


auditlog.register(Task)
