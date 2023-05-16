from post_deploy import post_deploy_action

from core.lib import is_schema_public
from core.models import Group


@post_deploy_action
def task():
    if is_schema_public():
        return

    for group in Group.objects.all():
        if 'members' not in group.plugins:
            group.plugins.append('members')
            group.save()