import logging

from django.core.management import BaseCommand

from concierge.api import fetch_mail_profile
from concierge.tasks import submit_user_token
from core.lib import is_schema_public
from user.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "DEV-Script to sync local users when the account backend changes."

    def handle(self, *args, **options):
        if is_schema_public():
            return

        for user in User.objects.all():
            self.update_user(user)
            self.sync_user(user)

    def update_user(self, user):
        try:
            data = fetch_mail_profile(user.email)
            if 'error' in data:
                if data.get('status_code') == 404:
                    user.external_id = None
                else:
                    raise Exception(data['error'])
            else:
                user.external_id = data.get('guid')
            user.save()
        except Exception as e:
            logger.error("update_user error %s at %s", e, user.email)

    def sync_user(self, user):
        try:
            assert user.external_id, "User has no external id."
            submit_user_token(user)
        except Exception as e:
            logger.error("sync_user error %s at %s", e, user.email)
