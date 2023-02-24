from django.db import models
from django.utils import timezone


class SiteInvitation(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class SiteAccessRequestQuerySet(models.QuerySet):

    def filter_accepted(self):
        return self.filter(accepted=True)

    def filter_pending(self):
        return self.filter(accepted=False)

    def last_modified_on_top(self):
        return self.order_by('-updated_at')

    def serialize(self):
        for record in self.all():
            yield {
                'email': record.email,
                'name': record.name,
                'status': 'accepted' if record.accepted else 'pending',
                'timeCreated': record.created_at,
                'timeUpdated': record.updated_at,
            }


class SiteAccessRequestManager(models.Manager):
    def get_queryset(self):
        return SiteAccessRequestQuerySet(self.model, using=self._db)

    def filter_accepted(self):
        return self.get_queryset().filter_accepted()

    def filter_pending(self):
        return self.get_queryset().filter_pending()

    def last_modified_on_top(self):
        return self.get_queryset().last_modified_on_top()

    def serialize(self):
        yield from self.get_queryset().serialize()


class SiteAccessRequest(models.Model):
    class Meta:
        ordering = ('created_at',)

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
