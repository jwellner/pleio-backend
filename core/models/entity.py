import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from model_utils.managers import InheritanceManager
from core.lib import get_acl
from core.constances import USER_ROLES
from .shared import read_access_default, write_access_default

class EntityManager(InheritanceManager):
    def visible(self, user):
        qs = self.get_queryset()
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))


class Entity(models.Model):
    objects = EntityManager()

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
    tags = ArrayField(models.CharField(max_length=256),
                      blank=True, default=list)

    def can_read(self, user):
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return True

        return len(get_acl(user) & set(self.read_access)) > 0

    def can_write(self, user):
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def guid(self):
        return str(self.id)

    class Meta:
        ordering = ['created_at']


class EntityView(models.Model):
    entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey('user.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)


class EntityViewCount(models.Model):
    entity = models.OneToOneField('core.Entity', on_delete=models.CASCADE, related_name="view_count")
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
