from django.utils.translation import gettext, activate
from post_deploy import post_deploy_action

from core import config
from core.lib import is_schema_public


@post_deploy_action
def translate_ban_reasons():
    if is_schema_public():
        return

    # TODO: lijkt net of ie het nog niet doet...

    activate(config.LANGUAGE)

    ban_reasons = {
        "Banned by admin": gettext("Blocked by admin"),
        "bouncing email adres": gettext('Bouncing e-mail address'),
        'user deleted in account': gettext('User deleted externally'),
        "banned": gettext('Removed by Profile-Sync'),
        "Deleted": gettext("Deleted"),
    }

    from user.models import User
    for user in User.objects.with_deleted().filter(is_active=False):
        user.ban_reason = ban_reasons.get(user.ban_reason) or user.ban_reason
        user.save()
