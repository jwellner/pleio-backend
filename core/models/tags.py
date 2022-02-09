from django.db import models

from core.constances import SYSTEM_TAGS

class ModelWithTagsManager(models.Manager):
    def __init__(self, exclude_archived = True):
        super().__init__()

        self.exclude_archived = exclude_archived

    def get_queryset(self):
        qs = super().get_queryset()
        if(self.exclude_archived):
            qs = qs.exclude(tags__contains=[SYSTEM_TAGS.ARCHIVED])

        return qs
