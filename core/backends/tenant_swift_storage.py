from swift.storage import SwiftStorage
from django_tenants.utils import parse_tenant_config_path


class TenantSwiftStorage(SwiftStorage):

    def __init__(self, *args, **kwargs):
        super(TenantSwiftStorage, self).__init__(*args, **kwargs)
        self.container_name = parse_tenant_config_path(self.container_name)
