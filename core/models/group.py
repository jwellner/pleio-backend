import uuid
from django.apps import apps
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from core.lib import ACCESS_TYPE
from core.constances import USER_ROLES

class GroupManager(models.Manager):
    def visible(self, user):
        if not user.is_authenticated:
            pass
        return self.get_queryset()

class Group(models.Model):
    class Meta:
        ordering = ['name']

    objects = GroupManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey('user.User', on_delete=models.PROTECT)

    name = models.CharField(max_length=200)

    description = models.TextField()
    rich_description = models.JSONField(null=True, blank=True)

    introduction = models.TextField(default='')
    welcome_message = models.TextField(default='')

    icon = models.ForeignKey(
        'file.FileFolder',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='group_icon'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    is_featured = models.BooleanField(default=False)
    featured_image = models.ForeignKey(
        'file.FileFolder',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='group_featured_image'
    )
    featured_video = models.CharField(max_length=256, null=True, blank=True)
    featured_position_y = models.IntegerField(null=True)

    is_closed = models.BooleanField(default=False)
    is_membership_on_request = models.BooleanField(default=False)
    is_leaving_group_disabled = models.BooleanField(default=False)
    is_auto_membership_enabled = models.BooleanField(default=False)

    auto_notification = models.BooleanField(default=False)

    tags = ArrayField(models.CharField(max_length=256),
                      blank=True, default=list)
    plugins = ArrayField(models.CharField(
        max_length=256), blank=True, default=list)

    def __str__(self):
        return self.name

    def is_member(self, user):
        if not user.is_authenticated:
            return False

        try:
            return self.members.filter(user=user).exists()
        except ObjectDoesNotExist:
            return False

    def is_full_member(self, user):
        if not user.is_authenticated:
            return False

        try:
            return self.members.filter(
                user=user,
                type__in=['admin', 'owner', 'member']
            ).exists()
        except ObjectDoesNotExist:
            return False

    def is_pending_member(self, user):
        if not user.is_authenticated:
            return False

        return self.members.filter(user=user, type='pending').exists()

    def can_write(self, user):
        if not user.is_authenticated:
            return False

        if user.has_role(USER_ROLES.ADMIN):
            return True

        if user == self.owner:
            return True

        return self.members.filter(user=user, type__in=['admin', 'owner']).exists()

    def join(self, user, member_type='member'):
        return self.members.update_or_create(
            user=user,
            defaults={
                'type': member_type,
                'enable_notification': self.auto_notification
            }
        )

    def leave(self, user):
        if self.subgroups:
            for subgroup in self.subgroups.all():
                if user in subgroup.members.all():
                    subgroup.members.remove(user)
        try:
            return self.members.get(user=user).delete()
        except ObjectDoesNotExist:
            return False

    def set_member_notification(self, user, notification=True):
        member = self.members.filter(user=user).first()
        if member:
            member.enable_notification = notification
            member.save()
            return True
        return False

    @property
    def guid(self):
        return str(self.id)

    @property
    def url(self):
        return "/groups/view/{}/{}".format(self.guid, slugify(self.name))

    @property
    def type_to_string(self):
        return 'group'

    @property
    def featured_image_url(self):
        if self.featured_image:
            return '%s?cache=%i' % (reverse('featured', args=[self.id]), int(self.featured_image.updated_at.timestamp()))
        return None

    def search_read_access(self):
        return [ACCESS_TYPE.public]


class GroupMembership(models.Model):
    class Meta:
        unique_together = ('user', 'group')
        ordering = ['group']

    MEMBER_TYPES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('pending', 'Pending')
    )

    user = models.ForeignKey(
        'user.User',
        related_name='memberships',
        on_delete=models.PROTECT
    )
    type = models.CharField(
        max_length=10,
        choices=MEMBER_TYPES,
        default='member'
    )
    group = models.ForeignKey(
        'core.Group',
        related_name='members',
        on_delete=models.CASCADE
    )
    enable_notification = models.BooleanField(default=False)

    def __str__(self):
        return "{} - {} - {}".format(
            self.user.name,
            self.type,
            self.group.name
        )


class GroupInvitation(models.Model):
    class Meta:
        unique_together = ('invited_user', 'group')

    group = models.ForeignKey(
        'core.Group',
        related_name='invitations',
        on_delete=models.CASCADE
    )
    invited_user = models.ForeignKey(
        'user.User',
        related_name='invitation',
        on_delete=models.CASCADE
    )

    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class Subgroup(models.Model):
    """
    A group of users within a group
    """

    name = models.CharField(max_length=512)
    members = models.ManyToManyField('user.User', related_name='subgroups')
    group = models.ForeignKey('core.Group', related_name='subgroups', on_delete=models.CASCADE)

    @property
    def access_id(self):
        return 10000 + self.id

@receiver([pre_save], sender=Group)
def update_entity_access(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    """
    Update Entity read_access when group is set to 'Closed'
    """
    if settings.IMPORTING:
        return

    if instance.is_closed:
        # to prevent cyclic import
        Entity = apps.get_model('core', 'Entity')

        filters = Q()
        filters.add(Q(group__id=instance.id), Q.AND)
        filters.add(Q(read_access__overlap=list([ACCESS_TYPE.public, ACCESS_TYPE.logged_in])), Q.AND)

        entities = Entity.objects.filter(filters)
        for entity in entities:
            if ACCESS_TYPE.public in entity.read_access:
                entity.read_access.remove(ACCESS_TYPE.public)
            if ACCESS_TYPE.logged_in in entity.read_access:
                entity.read_access.remove(ACCESS_TYPE.logged_in)
            if not ACCESS_TYPE.group.format(instance.id) in entity.read_access:
                entity.read_access.append(ACCESS_TYPE.group.format(instance.id))
            entity.save()
