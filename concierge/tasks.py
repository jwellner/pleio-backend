import logging
import uuid

import requests

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_tenants.utils import schema_context
from requests import RequestException, ConnectionError as RequestConnectionError

from concierge.api import fetch_profile
from concierge.constances import REGISTER_ORIGIN_SITE_URL, UPDATE_ORIGIN_SITE_URL
from core.lib import tenant_summary, get_account_url
from user.models import User

logger = logging.getLogger(__name__)


@shared_task
def profile_updated_signal(schema_name, origin_token, retry=3, retry_delay=60):
    with schema_context(schema_name):
        try:
            user = User.objects.get(_profile__origin_token=origin_token)
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

        except (AssertionError, RequestException) as e:
            logger.error(str(e))
            if retry > 0:
                profile_updated_signal.apply_async(kwargs={'schema_name': schema_name,
                                                           'origin_token': origin_token,
                                                           'retry': retry - 1,
                                                           'retry_delay': 10 * retry_delay},
                                                   eta=timezone.now() + timezone.timedelta(seconds=retry_delay))
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

            submit_user_token(schema, user)

    except AssertionError:
        pass


def submit_user_token(schema, user):
    try:
        token = uuid.uuid4()
        user.profile.update_origin_token(token)
        url = get_account_url(REGISTER_ORIGIN_SITE_URL.format(user.external_id))

        data = {'origin_token': token}
        data.update({f"origin_site_{key}": value for key, value in tenant_summary().items()})

        response = requests.post(url, data=data, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        }, timeout=10)
        if response.ok:
            profile_updated_signal.delay(schema, token)
        else:
            logger.error("Failed to sync a user origin_token for reason '%s'", response.reason)

    except RequestConnectionError as e:
        logger.warning("Error during submit_user_token: %s", repr(e))
        user.profile.update_origin_token(None)


@shared_task
def sync_user_registration_date(schema_name, user_id):
    try:
        with schema_context(schema_name):
            user = User.objects.get(id=user_id)
            submit_user_registration_date(user)
    except User.DoesNotExist:
        pass


def submit_user_registration_date(user):
    try:
        token = uuid.uuid4()
        user.profile.update_origin_token(token)
        url = get_account_url(REGISTER_ORIGIN_SITE_URL.format(user.external_id))

        data = {f"origin_site_{key}": value for key, value in tenant_summary().items()}
        data['registration_date'] = user.created_at

        response = requests.post(url, data=data, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        }, timeout=10)
        if not response.ok:
            logger.error("Failed to sync a user registration_date for reason '%s'", response.reason)

    except RequestConnectionError as e:
        logger.warning("Error during submit_user_registration_date: %s", repr(e))


@shared_task
def sync_site(schema_name):
    with schema_context(schema_name):
        try:
            url = get_account_url(UPDATE_ORIGIN_SITE_URL)
            data = {f"origin_site_{key}": value for key, value in tenant_summary().items()}

            response = requests.post(url, data=data, headers={
                'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
                'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
            }, timeout=10)
            if not response.ok:
                logger.error("Failed to sync new site attributes for reason: '%s'", response.reason)

        except RequestConnectionError as e:
            logger.warning("Error during sync site attributes: %s", repr(e))
