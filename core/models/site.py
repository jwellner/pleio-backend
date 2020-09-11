from django.db import models
from django.utils import timezone


class SiteInvitation(models.Model):

    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
