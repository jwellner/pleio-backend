from django.db import connections
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model


class ReadReplicaTenantMiddleware(TenantMainMiddleware):

    def get_tenant(self, domain_model, hostname):
        """Overwrites the default get_tenant to support disable active sites"""
        domain = domain_model.objects.select_related('tenant').get(domain=hostname, tenant__is_active=True)
        return domain.tenant

    def process_request(self, request):
        """Overwrites the django-tenant process_request middleware to support setting tenants on multiple databases"""
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.

        for con in connections:
            if "set_schema_to_public" in dir(connections[con]):
                connections[con].set_schema_to_public()
        hostname = self.hostname_from_request(request)

        domain_model = get_tenant_domain_model()
        try:
            tenant = self.get_tenant(domain_model, hostname)
        except domain_model.DoesNotExist:
            self.no_tenant_found(request, hostname)
            return

        tenant.domain_url = hostname
        request.tenant = tenant
        for con in connections:
            if "set_tenant" in dir(connections[con]):
                connections[con].set_tenant(request.tenant)

        self.setup_url_routing(request)