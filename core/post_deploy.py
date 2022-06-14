from django_tenants.utils import parse_tenant_config_path
from post_deploy import post_deploy_action

from core.elasticsearch import schedule_index_document
from user.models import User


@post_deploy_action
def schedule_index_users():
    if parse_tenant_config_path("") == 'public':
        return

    for user in User.objects.filter(is_active=True):
        schedule_index_document(user)