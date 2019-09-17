import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.mail import send_mail
from django.conf import settings
import reversion


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

    REQUIRED_FIELDS = ['name']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

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
