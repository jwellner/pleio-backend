import uuid
from auditlog.registry import auditlog
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .mixin import VoteMixin, CommentMixin
from .rich_fields import MentionMixin, AttachmentMixin
from core.constances import USER_ROLES
from core.lib import get_model_name, tenant_schema, datetime_utciso


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

    @property
    def guid(self):
        return str(self.id)

    @property
    def url(self):
        if self.container and hasattr(self.container, 'url'):
            return self.container.url
        return False

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

    def __str__(self):
        return f"Comment[{self.guid}]"

    def save(self, *args, **kwargs):
        created = self._state.adding
        super(Comment, self).save(*args, **kwargs)
        if created:
            self.create_notifications()

    def create_notifications(self):
        """ if comment is added to content, create a notification for all users following the content """
        from core.tasks import create_notification

        if self.owner:
            sender = self.owner.id
        else:
            return

        container = self.get_root_container()
        if container.update_last_action(self.created_at):
            container.save()

        if hasattr(container, 'add_follow'):
            container.add_follow(self.owner)

        create_notification.delay(tenant_schema(), 'commented', get_model_name(container), container.id, sender)

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

    def map_rich_text_fields(self, callback):
        self.rich_description = callback(self.rich_description)

    def serialize(self):
        return {
            'ownerGuid': self.owner.guid if self.owner else '',
            'name': self.owner.name if self.owner and not self.name else self.name,
            'email': self.owner.email if self.owner and not self.email else self.email,
            'richDescription': self.rich_description,
            'timeCreated': datetime_utciso(self.created_at),
            'containerGuid': str(self.container.id) if self.container else '',
        }


class CommentRequest(models.Model):
    code = models.CharField(max_length=36)

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    rich_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField(default=uuid.uuid4)
    container = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"CommentRequest[{self.name} commented on {self.container}]"


auditlog.register(Comment)
