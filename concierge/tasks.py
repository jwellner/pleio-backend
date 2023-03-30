import logging

from celery import shared_task
from django.core.exceptions import ValidationError
from django_tenants.utils import schema_context

from concierge.api import fetch_profile, sync_site as api_sync_site, submit_user_token
from user.models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, rate_limit="100/m", max_retries=3)
def profile_updated_signal(self, schema_name, user_id):
    with schema_context(schema_name):
        try:
            user = User.objects.get(id=user_id)
            data = fetch_profile(user)

            assert "error" not in data, data['error']

            user.external_id = data['guid']
            user.name = data['name']
            user.email = data['email']
            user.picture = data['avatarUrl']
            user.is_superadmin = data['isAdmin']
            if 'is_active' in data:
                user.is_active = data['is_active']
            user.save()

        except AssertionError as e:
            logger.error(str(e))
            if self.request.retries < self.max_retries:
                self.retry(countdown=100)
        except (User.DoesNotExist, ValidationError):
            pass


@shared_task
def sync_user(schema, user_id):
    try:
        with schema_context(schema):
            user = User.objects.get(id=user_id)

            assert user.is_active, "Inactive user"
            assert user.external_id, "User is not external"
            assert not user.profile.origin_token, "Already has a token"

            submit_user_token(user)

    except AssertionError:
        pass


@shared_task
def sync_site(schema_name):
    with schema_context(schema_name):
        api_sync_site()
