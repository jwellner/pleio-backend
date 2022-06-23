from django_tenants.utils import parse_tenant_config_path
from post_deploy import post_deploy_action

from core import config
from core.elasticsearch import schedule_index_document
from core.models import Group
from user.models import User


@post_deploy_action
def schedule_index_users():
    if parse_tenant_config_path("") == 'public':
        return

    for user in User.objects.filter(is_active=True):
        schedule_index_document(user)


@post_deploy_action
def sync_is_submit_updates_enabled_group_setting():
    """
    Copy the site setting for submit-updates in groups into the group setting.
    """
    if parse_tenant_config_path("") == 'public':
        return

    site_setting = config.STATUS_UPDATE_GROUPS
    for group in Group.objects.all():
        group.is_submit_updates_enabled = site_setting
        group.save()
