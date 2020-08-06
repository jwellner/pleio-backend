import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.lib import get_acl
from .shared import read_access_default, write_access_default


class UserProfile(models.Model):
    """
    Email overview intervals
    """
    INTERVALS = (
        ('never', 'Never'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('user.User', on_delete=models.CASCADE, related_name="_profile")
    last_online = models.DateTimeField(blank=True, null=True)
    receive_notification_email = models.BooleanField(default=False)
    overview_email_interval = models.CharField(
        max_length=10,
        choices=INTERVALS,
        default=None,
        blank=True,
        null=True
    )
    overview_email_tags = ArrayField(models.CharField(max_length=256),
                                     blank=True, default=list)
    overview_email_last_received = models.DateTimeField(blank=True, null=True)
    receive_newsletter = models.BooleanField(default=False)


class ProfileField(models.Model):
    """
    Profile field types
    """
    FIELD_TYPES = (
        ('select_field', 'SelectField'),
        ('date_field', 'DateField'),
        ('html_field', 'HTMLField'),
        ('multi_select_field', 'MultiSelectField'),
        ('text_field', 'TextField'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=512)
    category = models.CharField(max_length=512, blank=True, null=True)
    field_type = models.CharField(
        max_length=24,
        choices=FIELD_TYPES,
        default='text_field'
    )
    field_options = ArrayField(models.CharField(max_length=512),
                               blank=True, default=list)

    is_editable_by_user = models.BooleanField(default=True)
    is_filter = models.BooleanField(default=False)
    is_in_overview = models.BooleanField(default=False)
    is_in_onboarding = models.BooleanField(default=False)
    is_mandatory = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    @property
    def is_filterable(self):
        if self.field_type in ['date_field', 'html_field']:
            return False
        if self.field_type == 'text_field' and self.is_editable_by_user:
            return False
        return True


class UserProfileFieldManager(models.Manager):
    def visible(self, user):
        qs = self.get_queryset()
        if user.is_authenticated and user.is_admin:
            return qs
        return qs.filter(read_access__overlap=list(get_acl(user)))


class UserProfileField(models.Model):

    class META:
        unique_together = ('user_profile', 'profile_field')

    objects = UserProfileFieldManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, related_name="user_profile_fields")
    profile_field = models.ForeignKey('core.ProfileField', on_delete=models.CASCADE, related_name="profile_fields")
    value = models.CharField(max_length=4096)
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

    @property
    def name(self):
        return str(self.profile_field.name)

    @property
    def key(self):
        return str(self.profile_field.key)
