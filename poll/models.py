from django.db import models
from core.models import Object


class Poll(Object):
    class Meta:
        ordering = ['-id']

    title = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.title


class PollChoice(Object):
    poll = models.ForeignKey(Poll, on_delete=models.PROTECT)
    text = models.CharField(max_length=256)
    votes = models.IntegerField

    def __str__(self):
        return self.text
