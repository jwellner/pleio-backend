import uuid
import os
import time
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import reversion

from .lib import get_acl

class Manager(BaseUserManager):
    def create_user(self, email, name, password=None, external_id=None, is_active=False, picture=None):
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

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    external_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    picture = models.URLField(blank=True, null=True)

    groups = models.ManyToManyField('Group', through='GroupMembership')

    REQUIRED_FIELDS = ['name']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email or settings.FROM_EMAIL, [
                  self.email], **kwargs)

class Group(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=200)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_open = models.BooleanField(default=True)

    tags = ArrayField(models.CharField(max_length=256), blank=True, default=[])

    def __str__(self):
        return self.name

    def is_member(self, user):
        if not user.is_authenticated:
            return False

        try:
            return self.members.filter(user=user).exists()
        except ObjectDoesNotExist:
            return False

    def can_join(self, user):
        if not user.is_authenticated:
            return False

        if self.is_open or user.is_admin:
            return True

        return False

    def join(self, user):
        return self.members.update_or_create(user=user)

    def leave(self, user):
        try:
            return self.members.get(user=user).delete()
        except ObjectDoesNotExist:
            return False

class GroupMembership(models.Model):
    class Meta:
        unique_together = ('user', 'group')

    MEMBER_TYPES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member')
    )

    user = models.ForeignKey(User, related_name='members', on_delete=models.PROTECT)
    type = models.CharField(max_length=10, choices=MEMBER_TYPES, default='member')
    group = models.ForeignKey('Group', related_name='members', on_delete=models.PROTECT)

    def __str__(self):
        return "{} - {} - {}".format(self.user.name, self.type, self.group.name)

class Comment(models.Model):
    class Meta:
        ordering = ['-id']

    owner = models.ForeignKey(User, on_delete=models.PROTECT)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    container = GenericForeignKey('content_type', 'object_id')

    def can_write(self, user):
        if not user.is_authenticated:
            return False

        if user.is_admin:
            return True

        return (user == self.owner)

class ObjectManager(models.Manager):
    def visible(self, user):
        queryset = self.get_queryset()

        if user.is_authenticated and user.is_admin:
            return queryset

        return queryset.filter(read_access__overlap=list(get_acl(user)))

class Object(models.Model):
    objects = ObjectManager()
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT, blank=True, null=True)
    read_access = ArrayField(models.CharField(max_length=32), blank=True, default=['private'])
    write_access = ArrayField(models.CharField(max_length=32), blank=True, default=['private'])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = ArrayField(models.CharField(max_length=256), blank=True, default=[])

    def can_read(self, user):
        if user.is_authenticated and user.is_admin:
            return True

        return get_acl(user) in set(self.read_access)

    def can_write(self, user):
        if user.is_authenticated and user.is_admin:
            return True

        return get_acl(user) in set(self.write_access)

    class Meta:
        abstract = True
        ordering = ['created_at']

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('binary_file', time.strftime('%Y/%m/%d'), filename)

class BinaryFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    content_type = models.CharField(max_length=200)
    size = models.BigIntegerField(default=0)
    file = models.FileField(upload_to=get_file_path)
    created_at = models.DateTimeField(auto_now_add=True)
