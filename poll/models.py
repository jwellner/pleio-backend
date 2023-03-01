from auditlog.registry import auditlog
from django.db import models
from core.models import Entity, VoteMixin

from core.models.mixin import TitleMixin


class Poll(TitleMixin, Entity):
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Poll[{self.title}]"

    @property
    def type_to_string(self):
        return 'poll'

    @property
    def url(self):
        prefix = ''

        return '{}/polls/view/{}/{}'.format(
            prefix, self.guid, self.slug
        ).lower()

    def map_rich_text_fields(self, callback):
        pass

    def serialize(self):
        return {
            'title': self.title,
            **super().serialize(),
        }


class PollChoice(VoteMixin):
    class Meta:
        ordering = ['id']

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=256)

    def __str__(self):
        return f"PollChoice[{self.text}]"

    @property
    def guid(self):
        return str(self.id)


auditlog.register(Poll)
auditlog.register(PollChoice)
