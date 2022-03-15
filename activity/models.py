from auditlog.registry import auditlog
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from core.models import Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, AttachmentMixin
from core.utils.convert import tiptap_to_text

class StatusUpdate(Entity, VoteMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, AttachmentMixin):
    class Meta:
        ordering = ['-published']
        verbose_name = ugettext_lazy("status update")

    title = models.CharField(max_length=256, blank=True)
    rich_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"StatusUpdate[{self.guid}]"

    @property
    def type_to_string(self):
        return 'thewire'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}#{}'.format(
            prefix, self.guid
        ).lower()

    @property
    def rich_fields(self):
        return [self.rich_description]

    @property
    def description(self):
        return tiptap_to_text(self.rich_description)


auditlog.register(StatusUpdate)
