import uuid
import logging
from auditlog.registry import auditlog
from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils import timezone
from datetime import datetime
from core.lib import get_acl
from core.constances import USER_ROLES, ACCESS_TYPE
from core.exceptions import InvalidFieldException
from core import config
from core.utils.convert import tiptap_to_text
from .shared import read_access_default, write_access_default
from django.core.exceptions import ObjectDoesNotExist, ValidationError

logger = logging.getLogger(__name__)


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
    receive_notification_email = models.BooleanField(default=True)
    
    is_mention_notifications_enabled = models.BooleanField(default=True)
    is_mention_notification_direct_mail_enabled = models.BooleanField(default=False)
    is_mention_notification_push_enabled = models.BooleanField(default=False)

    is_comment_notifications_enabled = models.BooleanField(default=True)
    is_comment_notification_direct_mail_enabled = models.BooleanField(default=False)
    is_comment_notification_push_enabled = models.BooleanField(default=False)    

    notification_email_interval_hours = models.IntegerField(default=4)
    overview_email_interval = models.CharField(
        max_length=10,
        choices=INTERVALS,
        default=get_overview_email_interval_default,
        blank=True,
        null=True
    )
    overview_email_tags = ArrayField(models.CharField(max_length=256),
                                     blank=True, default=list)
    overview_email_categories = models.JSONField(blank=True, default=list)
    overview_email_last_received = models.DateTimeField(blank=True, null=True)
    receive_newsletter = models.BooleanField(default=False)
    language = models.CharField(
        max_length=10,
        default=None,
        blank=True,
        null=True
    )

    picture_file = models.ForeignKey(
        'file.FileFolder',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='picture_file'
    )

    origin_token = models.UUIDField(default=None, null=True, editable=False)

    def __str__(self):
        return f"UserProfile[{self.user.name}]"

    def update_origin_token(self, token):
        self.__class__.objects.filter(id=self.id).update(origin_token=token)

    def profile_field_value(self, field, current_user):
        field.value = ""
        field.read_access = []
        try:
            user_profile_field = self.user_profile_fields.visible(current_user).get(profile_field=field)
            field.value = field.sane_value(user_profile_field.value)
            field.read_access = user_profile_field.read_access
        except ObjectDoesNotExist:
            field.read_access = [ACCESS_TYPE.logged_in]
        return field

    def index_instance(self):
        """ Return the object that will put changes to me in the search index."""
        return self.user

    def picture_path(self):
        try:
            return self.picture_file.upload.path
        except Exception:
            pass


class ProfileFieldValidator(models.Model):
    """
    Profile field validator
    """

    class Meta:
        ordering = ['created_at', 'id']

    VALIDATOR_TYPES = (
        ('inList', 'inList'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    validator_data = models.JSONField(null=True, blank=True, help_text="Please provide valid JSON data")

    validator_type = models.CharField(
        max_length=24,
        choices=VALIDATOR_TYPES,
        blank=False
    )

    created_at = models.DateTimeField(default=timezone.now)

    def validate(self, value):
        if self.validator_type == 'inList':
            if value in self.validator_data:
                return True
        return False


class ProfileFieldManager(models.Manager):
    def get_date_field(self, guid):
        try:
            profile_field = self.get_queryset().get(id=guid)
        except ObjectDoesNotExist:
            raise InvalidFieldException()

        if not profile_field.field_type == "date_field":
            raise InvalidFieldException()

        return profile_field


class ProfileField(models.Model):
    """
    Profile field types
    """

    class Meta:
        ordering = ['created_at', 'id']

    FIELD_TYPES = (
        ('select_field', 'select_field'),
        ('date_field', 'date_field'),
        ('html_field', 'html_field'),
        ('multi_select_field', 'multi_select_field'),
        ('text_field', 'text_field'),
    )

    objects = ProfileFieldManager()

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
    is_on_vcard = models.BooleanField(default=False)
    is_mandatory = models.BooleanField(default=False)

    validators = models.ManyToManyField('core.ProfileFieldValidator', related_name="profile_fields")

    created_at = models.DateTimeField(default=timezone.now)

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

    def __str__(self):
        return f"ProfileField[{self.name}]"

    def sane_value(self, value):
        if self.field_type == 'multi_select_field':
            return ",".join([s.strip() for s in filter(lambda x: x.strip() in self.field_options, value.split(','))])
        return value

    def validate(self, value):
        if value:
            for validator in self.validators.all():
                if not validator.validate(value):
                    return False
        return True

    def clean(self):
        if self.field_type == 'html_field' and self.is_on_vcard:
            raise ValidationError("is_on_vcard=True is not allowed for %s" % self.field_type)
        if self.field_type == 'html_field' and self.is_filter:
            raise ValidationError("is_filter=True is not allowed for %s" % self.field_type)
        if self.field_type == 'html_field' and self.is_in_overview:
            raise ValidationError("is_in_overview=True is not allowed for %s" % self.field_type)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ProfileField, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(ProfileField, self).delete(*args, **kwargs)
        config.PROFILE_SECTIONS = validate_profile_sections(config.PROFILE_SECTIONS)


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
    class Meta:
        unique_together = ('user_profile', 'profile_field')

    objects = UserProfileFieldManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, related_name="user_profile_fields")
    profile_field = models.ForeignKey('core.ProfileField', on_delete=models.CASCADE, related_name="profile_fields")
    value = models.TextField()
    value_date = models.DateField(default=None, blank=True, null=True)
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
            return tiptap_to_text(self.value)

        return self.value

    @property
    def value_list_field_indexing(self):
        """Format value list according to type"""
        if self.profile_field.field_type == "multi_select_field":
            return self.value.split(',')
        return []

    @property
    def is_empty(self):
        if self.profile_field.field_type == 'date_field':
            return self.value_date is None
        return self.value is None or self.value == ''

    def __str__(self):
        return f"UserProfileField[{self.profile_field.name}]"

    def save(self, *args, **kwargs):
        self.set_date_field_value()
        super(UserProfileField, self).save(*args, **kwargs)

    def index_instance(self):
        return self.user_profile.index_instance()

    def set_date_field_value(self):
        if self.profile_field.field_type == "date_field":
            try:
                self.value_date = datetime.strptime(self.value, '%Y-%m-%d')
            except Exception:
                self.date_value = None


auditlog.register(UserProfile, exclude_fields=['last_online'])
auditlog.register(ProfileField)
auditlog.register(UserProfileField)
