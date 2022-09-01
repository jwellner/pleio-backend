from post_deploy import post_deploy_action

from core.lib import tenant_schema, is_schema_public
from user.models import User


@post_deploy_action(auto=False)
def sync_site_attributes():
    if is_schema_public():
        return

    from .tasks import sync_site
    sync_site(tenant_schema())


@post_deploy_action(auto=False)
def sync_user_registration_date():
    from concierge.tasks import sync_user_registration_date

    if is_schema_public():
        return

    for user in User.objects.filter(is_active=True):
        sync_user_registration_date.delay(tenant_schema(), str(user.id))
