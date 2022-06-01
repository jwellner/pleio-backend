from django_tenants.utils import parse_tenant_config_path
from post_deploy import post_deploy_action


@post_deploy_action(auto=False)
def sync_site_attributes():
    if parse_tenant_config_path("") == 'public':
        return
    # pylint: disable=import-outside-toplevel
    from .tasks import sync_site
    sync_site(parse_tenant_config_path(""))
