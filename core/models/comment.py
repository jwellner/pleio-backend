import uuid
from auditlog.registry import auditlog
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .annotation import VoteMixin
from core.constances import USER_ROLES


class CommentManager(models.Manager):
    def visible(self):
        queryset = self.get_queryset()

        return queryset

class Comment(VoteMixin):
    class Meta:
        ordering = ['-created_at']
    objects = CommentManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('user.User', on_delete=models.PROTECT, null=True, blank=True)

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    container = GenericForeignKey('content_type', 'object_id')

    def can_write(self, user):
        if not user.is_authenticated:
            return False

        if user.has_role(USER_ROLES.ADMIN):
            return True

        return (user == self.owner)

    def can_read(self, user):
        if self.container and hasattr(self.container, 'can_read'):
            return self.container.can_read(user)
        return False

    @property
    def guid(self):
        return str(self.id)

    @property
    def url(self):
        if self.container and hasattr(self.container, 'url'):
            return self.container.url
        return False

    def __str__(self):
        return f"Comment[{self.guid}]"

class CommentRequest(models.Model):

    code = models.CharField(max_length=36)

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    container = GenericForeignKey('content_type', 'object_id')

class CommentMixin(models.Model):
    comments = GenericRelation(Comment)

    def can_comment(self, user):
        if not user.is_authenticated:
            return False

        return True

    class Meta:
        abstract = True


auditlog.register(Comment)