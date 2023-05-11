from post_deploy import post_deploy_action

from core.lib import is_schema_public
from core.models import Group


@post_deploy_action
def task():
    if is_schema_public():
        return

    for group in Group.objects.all():
        current_widgets = [w.get('type') for w in group.widget_repository or []]
        if 'events' not in current_widgets:
            group.widget_repository = [{'type': "events", 'settings': []}, *group.widget_repository]
            group.save()
        if 'groupMembers' not in current_widgets:
            group.widget_repository = [{'type': "groupMembers", 'settings': []}, *group.widget_repository]
            group.save()
