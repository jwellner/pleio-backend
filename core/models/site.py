from django.db import models
from django.utils import timezone


class SiteInvitation(models.Model):

    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class SiteAccessRequest(models.Model):

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=100)

    claims = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)