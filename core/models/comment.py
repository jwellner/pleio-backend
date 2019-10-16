import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .annotation import VoteMixin

class CommentManager(models.Manager):
    def visible(self):
        queryset = self.get_queryset()

        return queryset

class Comment(VoteMixin):
    class Meta:
        ordering = ['created_at']
    objects = CommentManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('core.User', on_delete=models.PROTECT)

    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    container = GenericForeignKey('content_type', 'object_id')

    def can_write(self, user):
        if not user.is_authenticated:
            return False

        if user.is_admin:
            return True

        return (user == self.owner)

    @property
    def guid(self):
        return str(self.id)

class CommentMixin(models.Model):
    comments = GenericRelation(Comment)

    def can_comment(self, user):
        if not user.is_authenticated:
            return False

        return True

    class Meta:
        abstract = True
