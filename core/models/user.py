import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from core.lib import get_acl, draft_to_text
from core.constances import USER_ROLES
from core import config
from .shared import read_access_default, write_access_default


def get_overview_email_interval_default():
    return config.EMAIL_OVERVIEW_DEFAULT_FREQUENCY

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
        default=get_overview_email_interval_default,
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

    @property
    def is_filterable(self):
        if self.field_type in ['date_field', 'html_field']:
            return False
        if self.field_type == 'text_field' and self.is_editable_by_user:
            return False
        return True

    # TODO: look if possible to remove this
    @property
    def category(self):
        for section in config.PROFILE_SECTIONS:
            if str(self.id) in section['profileFieldGuids']:
                return section['name']
        return None

    @property
    def guid(self):
        return str(self.id)


class UserProfileFieldManager(models.Manager):
    def visible(self, user):
        qs = self.get_queryset()
        if user.is_authenticated and user.has_role(USER_ROLES.ADMIN):
            return qs
        return qs.filter(read_access__overlap=list(get_acl(user)))


def validate_profile_sections(sections):
    profile_sections = []
    for section in sections:
        guids = []
        for guid in section['profileFieldGuids']:
            try:
                guids.append(ProfileField.objects.get(id=guid).guid)
            except Exception:
                continue
        profile_sections.append({'name': section['name'], 'profileFieldGuids': guids})
    return profile_sections


class UserProfileField(models.Model):

    class META:
        unique_together = ('user_profile', 'profile_field')

    objects = UserProfileFieldManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, related_name="user_profile_fields")
    profile_field = models.ForeignKey('core.ProfileField', on_delete=models.CASCADE, related_name="profile_fields")
    value = models.TextField()
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

    @property
    def value_field_indexing(self):
        """Format value according to type"""
        if self.profile_field.field_type == "html_field":
            return draft_to_text(self.value)

        return self.value


@receiver(post_delete, sender=ProfileField)
def validate_config_profile_sections(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    config.PROFILE_SECTIONS = validate_profile_sections(config.PROFILE_SECTIONS)
