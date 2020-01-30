import uuid
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
import reversion
from core.lib import ACCESS_TYPE, get_acl
from .shared import read_access_default, write_access_default


class Manager(BaseUserManager):
    def visible(self, user):
        if not user.is_authenticated:
            return self.get_queryset().none()
        return self.get_queryset()

    def create_user(
            self,
            email,
            name,
            password=None,
            external_id=None,
            is_active=False,
            picture=None,
            is_government=False,
            has_2fa_enabled=False):
        # pylint: disable=too-many-arguments
        # pylint: disable=unused-argument
        if not email:
            raise ValueError('Users must have an email address')

        with reversion.create_revision():
            user = self.model(
                email=self.normalize_email(email),
                name=name
            )

            if password:
                user.set_password(password)

            if external_id:
                user.external_id = external_id

            if picture:
                user.picture = picture

            if is_government:
                user.is_government = is_government

            if has_2fa_enabled:
                user.has_2fa_enabled = has_2fa_enabled

            user.save(using=self._db)

            reversion.set_comment("New user created")

        return user

    def create_superuser(self, email, name, password):
        with reversion.create_revision():
            user = self.create_user(
                email=self.normalize_email(email),
                name=name,
                password=password
            )

            user.is_admin = True
            user.is_active = True
            user.save(using=self._db)

            reversion.set_comment("Superuser created.")

        return user


class User(AbstractBaseUser):
    objects = Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    external_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    picture = models.URLField(blank=True, null=True)
    is_government = models.BooleanField(default=False)
    has_2fa_enabled = models.BooleanField(default=False)
    is_delete_requested = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['name']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    @property
    def type_to_string(self):
        return 'user'

    @property
    def url(self):
        return "/user/{}/profile".format(self.guid)

    def search_read_access(self):
        return [ACCESS_TYPE.logged_in]

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        # pylint: disable=unused-argument
        return True

    def has_module_perms(self, app_label):
        # pylint: disable=unused-argument
        return True

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    @property
    def guid(self):
        return str(self.id)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email or settings.FROM_EMAIL, [
                  self.email], **kwargs)

    @property
    def profile(self):
        try:
            return self._profile
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(
                user=self,
            )


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
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name="_profile")
    last_online = models.DateTimeField(blank=True, null=True)
    receive_notification_email = models.BooleanField(default=False)
    group_notifications = ArrayField(models.CharField(max_length=64),
                                     blank=True, default=list)
    overview_email_interval = models.CharField(
        max_length=10,
        choices=INTERVALS,
        default='weekly'
    )
    receive_newsletter = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    if created:
        UserProfile.objects.create(user=instance)


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
