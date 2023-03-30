from celery.utils.log import get_task_logger
from post_deploy import post_deploy_action

from concierge.api import fetch_mail_profile
from core.lib import tenant_schema, is_schema_public
from user.models import User

logger = get_task_logger(__name__)


@post_deploy_action(auto=False)
def sync_site_attributes():  # pragma: no cover
    if is_schema_public():
        return

    from .tasks import sync_site
    sync_site(tenant_schema())


@post_deploy_action(auto=False)
def sync_user_avatars():  # pragma: no cover
    if is_schema_public():
        return

    users = User.objects.all()
    users = users.exclude(picture__contains='/avatar/')
    users = users.exclude(picture__isnull=True)
    for user in users:
        try:
            data = fetch_mail_profile(user.email)
            assert 'error' not in data, data['error']

            if 'avatarUrl' in data:
                user.picture = data['avatarUrl']
                user.save()
                logger.info("Updated details for %s", user.id)
        except Exception as e:
            logger.error("Error at sync_user_profiles at %s|%s with error %s message %s", user.email, tenant_schema(), e.__class__, e)
