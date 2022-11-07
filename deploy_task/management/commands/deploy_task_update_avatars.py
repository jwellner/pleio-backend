import logging
import requests

from concierge.api import fetch_avatar
from deploy_task.utils import DeployCommandBase
from user.models import User

logger = logging.getLogger(__name__)


def verify_all_accounts():
    for user in User.objects.filter(is_active=True):
        try:
            if user.picture:
                response = requests.get(user.picture, timeout=10)
                if response.status_code == 404:
                    result = fetch_avatar(user)
                    if result.get('originalAvatarUrl') is None:
                        user.profile.picture_file = None
                        user.profile.save()
                        user.picture = None
                        user.save()
                    else:
                        user.picture = result.get('avatarUrl')
                        user.save()
        except Exception as e:
            logger.error(str(e))
            logger.error(str(e.__class__))


class Command(DeployCommandBase):
    deploy_task = verify_all_accounts
