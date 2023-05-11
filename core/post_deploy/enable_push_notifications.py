from post_deploy import post_deploy_action

from core import config
from core.lib import is_schema_public


@post_deploy_action
def task():
    if is_schema_public():
        return

    config.PUSH_NOTIFICATIONS_ENABLED = True
