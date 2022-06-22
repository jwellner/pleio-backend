import uuid
from auditlog.registry import auditlog
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .mixin import VoteMixin, CommentMixin
from .rich_fields import MentionMixin, AttachmentMixin
from core.constances import USER_ROLES

class CommentManager(models.Manager):
    def visible(self):
        queryset = self.get_queryset()

        return queryset

class Comment(VoteMixin, MentionMixin, AttachmentMixin, CommentMixin):
    class Meta:
        ordering = ['-created_at']
    objects = CommentManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('user.User', on_delete=models.PROTECT, null=True, blank=True)

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

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

    def get_root_container(self, parent=None):
        if not parent:
            parent = self.container
        if isinstance(parent, Comment):
            return self.get_root_container(parent.container)
        return parent

    def index_instance(self):
        return self.get_root_container()

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

    @property
    def rich_fields(self):
        return [self.rich_description]

    @property
    def group(self):
        if self.container and hasattr(self.container, 'group'):
            return self.container.group

        return None

    @property
    def type_to_string(self):
        return 'comment'

    @property
    def title(self):
        if self.container and hasattr(self.container, 'title'):
            return self.container.title

        return ''


class CommentRequest(models.Model):

    code = models.CharField(max_length=36)

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    rich_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    container = GenericForeignKey('content_type', 'object_id')


auditlog.register(Comment)
