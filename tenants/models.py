import uuid

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone


class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # database used for migration
    elgg_database = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    @property
    def primary_domain(self):
        primary = self.get_primary_domain()
        if primary:
            return primary.domain
        return None


class Domain(DomainMixin):
    pass


class GroupCopy(models.Model):
    STATE_TYPES = (
        ('PENDING', 'PENDING'),
        ('STARTED', 'STARTED'),
        ('RETRY', 'RETRY'),
        ('FAILURE', 'FAILURE'),
        ('SUCCESS', 'SUCCESS'),
    )

    source_tenant =  models.CharField(max_length=200)
    target_tenant = models.CharField(max_length=200)

    action_user_id = models.UUIDField(default=uuid.uuid4, editable=False)
    source_id = models.UUIDField(default=uuid.uuid4, editable=False)
    target_id = models.UUIDField(default=uuid.uuid4, editable=False)

    task_id = models.CharField(max_length=200, null=True)
    task_state = models.CharField(
        max_length=16,
        choices=STATE_TYPES,
        default='PENDING'
    )
    task_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']



class GroupCopyMapping(models.Model):
    
    copy = models.ForeignKey(
        'tenants.GroupCopy',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='mapping'
    )

    entity_type = models.CharField(max_length=200)

    source_id = models.UUIDField(default=uuid.uuid4, editable=False)
    target_id = models.UUIDField(default=uuid.uuid4, editable=False)

    created = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
