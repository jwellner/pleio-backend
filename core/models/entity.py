import uuid
from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from model_utils.managers import InheritanceManager
from core.lib import get_acl
from core.constances import ENTITY_STATUS, USER_ROLES
from .shared import read_access_default, write_access_default


class EntityManager(InheritanceManager):
    def __init__(self, exclude_archived = True):
        super().__init__()

        self.exclude_archived = exclude_archived

    def get_queryset(self):
        qs = super().get_queryset()
        if(self.exclude_archived):
            qs = qs.exclude(is_archived=True)

        return qs

    def draft(self, user):
        qs = self.get_queryset()
        if not user.is_authenticated:
            return qs.none()

        qs = qs.filter(
            Q(published__gt=timezone.now()) |
            Q(published__isnull=True)
        )

        if user.has_role(USER_ROLES.ADMIN):
            return qs

        return qs.filter(owner=user)

    def published(self):
        qs = self.get_queryset()
        return qs.filter(published__lte=timezone.now())

    def visible(self, user):
        qs = self.published()
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))


class Entity(models.Model):
    objects = EntityManager()
    all_objects = EntityManager(exclude_archived=False)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('user.User', on_delete=models.PROTECT)
    group = models.ForeignKey(
        'core.Group',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    read_access = ArrayField(
        models.CharField(max_length=64),
        blank=True,
        default=read_access_default
    )
    write_access = ArrayField(
        models.CharField(max_length=64),
        blank=True,
        default=write_access_default
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    last_action = models.DateTimeField(default=timezone.now)

    published = models.DateTimeField(default=timezone.now, null=True)
    is_archived = models.BooleanField(default=False)
    tags = ArrayField(models.CharField(max_length=256),
                      blank=True, default=list)

    notifications_created = models.BooleanField(default=False)

    is_pinned = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)

    def can_read(self, user):
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return True

        if self.group and self.group.is_closed and not self.group.is_full_member(user):
            return False

        return len(get_acl(user) & set(self.read_access)) > 0

    def can_write(self, user):
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return True

        if user.is_authenticated and self.group and self.group.members.filter(user=user, type__in=['admin', 'owner']).exists():
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def guid(self):
        return str(self.id)

    @property
    def status_published(self):
        if self.is_archived:
            return ENTITY_STATUS.ARCHIVED

        if self.published and self.published < timezone.now():
            return ENTITY_STATUS.PUBLISHED

        return ENTITY_STATUS.DRAFT

    class Meta:
        ordering = ['published']


class EntityView(models.Model):
    entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey('user.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)


class EntityViewCount(models.Model):
    entity = models.OneToOneField('core.Entity', on_delete=models.CASCADE, related_name="view_count")
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
