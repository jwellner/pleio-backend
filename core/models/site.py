from django.db import models
from django.utils import timezone


class SiteInvitation(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class SiteAccessRequestManager(models.Manager):
    """ Separate manager for unit-testing purposes. """


class SiteAccessRequest(models.Model):
    objects = SiteAccessRequestManager()

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=100)

    claims = models.JSONField(null=True, blank=True)

    accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class SiteStat(models.Model):
    STAT_TYPES = (
        ('DISK_SIZE', 'DISK_SIZE'),
        ('DB_SIZE', 'DB_SIZE'),
    )

    stat_type = models.CharField(
        max_length=16,
        choices=STAT_TYPES,
        default='DISK_SIZE'
    )

    value = models.BigIntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
