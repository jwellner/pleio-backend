from django.db import connections
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model


class PleioTenantMiddleware(TenantMainMiddleware):

    def get_tenant(self, domain_model, hostname):
        """Overwrites the default get_tenant to support disable active sites"""
        domain = domain_model.objects.select_related('tenant').get(domain=hostname, tenant__is_active=True)
        return domain.tenant
