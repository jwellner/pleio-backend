import logging
import uuid

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from model_utils.managers import InheritanceManager
from core.lib import get_acl
from core.constances import ENTITY_STATUS, USER_ROLES
from core.models.shared import read_access_default, write_access_default
from .tags import TagsMixin

logger = logging.getLogger(__name__)


class EntityManager(InheritanceManager):

    def status_published(self, filter_status, user=None):
        user = user or AnonymousUser()
        public_possible = False
        acl = get_acl(user)
        query = Q()

        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            access = Q()
        else:
            access = Q(read_access__overlap=list(acl))

        if ENTITY_STATUS.PUBLISHED in filter_status:
            not_archived = Q(is_archived__isnull=True) | Q(is_archived=False)
            query.add(Q(published__lte=timezone.now()) & access & not_archived, Q.OR)
            public_possible = True

        if ENTITY_STATUS.ARCHIVED in filter_status:
            query.add(Q(is_archived=True) & access, Q.OR)
            public_possible = True

        if not user.is_authenticated and not public_possible:
            return self.get_queryset().none()

        if ENTITY_STATUS.DRAFT in filter_status:
            draft_query = Q(Q(published__gt=timezone.now()) |
                            Q(published__isnull=True))
            if not user.has_role(USER_ROLES.ADMIN):
                draft_query.add(Q(owner=user), Q.AND)

            query.add(draft_query, Q.OR)

        return self.get_queryset().filter(query)


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

    def archived(self, user):
        qs = self.get_queryset().filter(is_archived=True)

        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))

    def published(self):
        qs = self.get_queryset()
        return qs.filter(published__lte=timezone.now(), is_archived=False)

    def visible(self, user):
        qs = self.published()
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return qs

        return qs.filter(read_access__overlap=list(get_acl(user)))


class Entity(models.Model, TagsMixin):
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
    last_action = models.DateTimeField(default=timezone.now)

    published = models.DateTimeField(default=timezone.now, null=True)
    is_archived = models.BooleanField(default=False)
    schedule_archive_after = models.DateTimeField(null=True, blank=True)
    schedule_delete_after = models.DateTimeField(null=True, blank=True)

    _tag_summary = ArrayField(models.CharField(max_length=256),
                              blank=True, default=list,
                              db_column='tags')
    
    related_items = ArrayField (models.UUIDField(default=uuid.uuid4),
                                blank=True, null=True)

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

        if user.is_authenticated and self.group and self.group.members.filter(user=user,
                                                                              type__in=['admin', 'owner']).exists():
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
    viewer = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="viewed_entities",
                               null=True, blank=True, default=None)
    session = models.TextField(max_length=128, null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)


class EntityViewCount(models.Model):
    entity = models.OneToOneField('core.Entity', on_delete=models.CASCADE, related_name="view_count")
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
