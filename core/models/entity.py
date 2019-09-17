import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from model_utils.managers import InheritanceManager
from core.lib import get_acl
from . import User, Group
from .shared import read_access_default, write_access_default

class EntityManager(InheritanceManager):
    def visible(self, user):
        qs = self.get_queryset()
        if user.is_authenticated and user.is_admin:
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))


class Entity(models.Model):
    objects = EntityManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    read_access = ArrayField(
        models.CharField(max_length=32),
        blank=True,
        default=read_access_default
    )
    write_access = ArrayField(
        models.CharField(max_length=32),
        blank=True,
        default=write_access_default
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = ArrayField(models.CharField(max_length=256),
                      blank=True, default=list)

    def can_read(self, user):
        if user.is_authenticated and user.is_admin:
            return True

        return len(get_acl(user) & set(self.read_access)) > 0

    def can_write(self, user):
        if user.is_authenticated and user.is_admin:
            return True

        return len(get_acl(user) & set(self.write_access)) > 0

    @property
    def guid(self):
        return str(self.id)

    class Meta:
        ordering = ['created_at']
