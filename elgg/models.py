from django.db import models


class GuidMap(models.Model):
    """
    Used for redirecting old ELGG id's
    """
    id = models.BigAutoField(primary_key=True)
    guid = models.UUIDField(unique=True)
    object_type = models.CharField(max_length=32)


class FriendlyUrlMap(models.Model):
    """
    Used for redirecting old ELGG entity friendly URLs
    """
    id = models.BigAutoField(primary_key=True)
    object_id = models.UUIDField()
    url = models.URLField(max_length=1024, unique=True)
