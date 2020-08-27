import uuid
from core.models import UserProfile
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone


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

        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(
            email=self.normalize_email(email),
            name=name,
            password=password
        )

        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)

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
    ban_reason = models.CharField(max_length=100, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

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
        return ['logged_in']

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
            if not settings.RUN_AS_ADMIN_APP:
                return UserProfile.objects.create(
                    user=self,
                )

    def delete(self, using='', keep_parents=False):
        self.is_active = False
        self.email = "%s@deleted" % self.guid
        self.name = "Verwijderde gebruiker"
        self.external_id = None
        self.picture = None
        self.is_government = False
        self.has_2fa_enabled = False
        self.ban_reason = "Deleted"
        # delete user profile data
        try:
            self._profile.delete()
        except UserProfile.DoesNotExist:
            pass

        self.notifications.all().delete()

        self.save()

        return True

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    if settings.IMPORTING:
        return
    if not settings.RUN_AS_ADMIN_APP and created:
        UserProfile.objects.create(user=instance)
