import uuid

from django.db import models, connection
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone
from django.urls import reverse
from uuslug import uuslug


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


class Agreement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class AgreementVersion(models.Model):
    class Meta:
        ordering = ['created_at']
    agreement = models.ForeignKey(
        'tenants.Agreement',
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version = models.CharField(max_length=100)
    slug = models.SlugField(null=False, unique=True)
    document = models.FileField(upload_to='agreements')
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def accepted_for_current_tenant(self):
        return self.accepted_for_tenant(connection.schema_name)

    def accepted_for_tenant(self, tenant):
        tenant = Client.objects.get(schema_name=tenant)
        return self.accepted.filter(client=tenant).first()

    def __str__(self):
        return f"{self.agreement.name} {self.version}"

    def get_absolute_url(self):
        return reverse("agreement", kwargs={"slug": self.slug})
    
    def save(self, *args, **kwargs):
        self.slug = uuslug(str(self), instance=self)
        super(AgreementVersion, self).save(*args, **kwargs)

class AgreementAccept(models.Model):
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
    )

    agreement_version = models.ForeignKey(
        'tenants.AgreementVersion',
        on_delete=models.CASCADE,
        related_name='accepted'
    )

    accept_name = models.CharField(max_length=100)
    accept_user_id = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.client.name} {self.accept_name}"