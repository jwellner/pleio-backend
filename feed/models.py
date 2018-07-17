from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.models import ContentType
from django.db import models
from core.lib import get_acl

class FeedManager(models.Manager):
    def visible(self, user):
        queryset = self.get_queryset()

        if user.is_authenticated and user.is_admin:
            return queryset

        return queryset.filter(read_access__contained_by=list(get_acl(user)))

class Feed(models.Model):
    objects = FeedManager()

    read_access = ArrayField(models.CharField(max_length=32), blank=True, default=['private'])
    write_access = ArrayField(models.CharField(max_length=32), blank=True, default=['private'])

    created_at = models.DateTimeField(auto_now_add=True)

    node_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    node_id = models.PositiveIntegerField()
    node = GenericForeignKey('node_type', 'node_id')

    def __str__(self):
        return '{}:{}'.format(self.node_type, self.node_id)