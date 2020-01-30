import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ObjectDoesNotExist
from core.lib import ACCESS_TYPE

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

    owner = models.ForeignKey('core.User', on_delete=models.PROTECT)

    name = models.CharField(max_length=200)

    description = models.TextField()
    rich_description = JSONField(null=True, blank=True)

    introduction = models.TextField(default='')
    welcome_message = models.TextField(default='')

    icon = models.CharField(max_length=200, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_featured = models.BooleanField(default=False)
    featured_image = models.CharField(max_length=256, null=True, blank=True)
    featured_video = models.CharField(max_length=256, null=True, blank=True)
    featured_position_y = models.IntegerField(null=True)

    is_closed = models.BooleanField(default=False)
    is_membership_on_request = models.BooleanField(default=False)

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

        if user.is_admin:
            return True

        if user == self.owner:
            return True

        return self.members.filter(user=user, type__in=['admin', 'owner']).exists()

    def join(self, user, member_type):
        return self.members.update_or_create(
            user=user,
            defaults={'type': member_type}
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

    @property
    def guid(self):
        return str(self.id)

    def type_to_string(self):
        return 'group'

    def search_read_access(self):
        return [ACCESS_TYPE.public]


class GroupMembership(models.Model):
    class Meta:
        unique_together = ('user', 'group')

    MEMBER_TYPES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('pending', 'Pending')
    )

    user = models.ForeignKey(
        'User',
        related_name='memberships',
        on_delete=models.PROTECT
    )
    type = models.CharField(
        max_length=10,
        choices=MEMBER_TYPES,
        default='member'
    )
    group = models.ForeignKey(
        'Group',
        related_name='members',
        on_delete=models.CASCADE
    )

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
        'Group',
        related_name='invitations',
        on_delete=models.CASCADE
    )
    invited_user = models.ForeignKey(
        'User',
        related_name='invitation',
        on_delete=models.CASCADE
    )

    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Subgroup(models.Model):
    """
    A group of users within a group
    """
    #TODO: access_id is same as id, now it conflicts with some of core access_ids, ie 0,1,2,4. Solution needed

    name = models.CharField(max_length=512)
    members = models.ManyToManyField('core.User', related_name='subgroups')
    group = models.ForeignKey('core.Group', related_name='subgroups', on_delete=models.CASCADE)

    @property
    def access_id(self):
        return 10000 + self.id
