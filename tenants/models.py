from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


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
