import logging
import uuid

import requests

from celery import shared_task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_tenants.utils import schema_context
from requests import RequestException, ConnectionError as RequestConnectionError

from tenants.models import Client
from user.models import User

logger = logging.getLogger(__name__)

FETCH_PROFILE_URL = "{}/api/users/fetch_profile/{}"


@shared_task
def profile_updated_signal(schema_name, origin_token, retry=3, retry_delay=60):
    with schema_context(schema_name):
        try:
            user = User.objects.get(_profile__origin_token=origin_token)
            response = requests.get(FETCH_PROFILE_URL.format(str(settings.ACCOUNT_API_URL).rstrip('/'),
                                                             user.external_id),
                                    headers={'X-Origin-Token': str(user.profile.origin_token)})

            assert response.ok, response.reason

            data = response.json()
            user.name = data['name']
            user.email = data['email']
            user.picture = data['avatarUrl']
            user.is_superadmin = data['isAdmin']
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
        origin = Client.objects.get(schema_name=schema)
        user.profile.update_origin_token(token)
        url = "{}/api/users/register_origin_site/{}".format(
            settings.ACCOUNT_API_URL, user.external_id,
        )

        url_schema = "http" if settings.ENV == 'local' else "https"
        url_port = ":8000" if settings.ENV == 'local' else ""

        data = {
            'origin_site_url': "{}://{}{}".format(url_schema, origin.primary_domain, url_port),
            'origin_site_name': origin.name,
            'origin_token': token,
        }
        response = requests.post(url, data=data, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        })
        if not response.ok:
            logger.warning("Failed to sync a user origin_token for reason '%s'", response.reason)

        profile_updated_signal.delay(schema, token)

    except RequestConnectionError as e:
        # Allow retry next time.
        user.profile.update_origin_token(None)
        logger.warning("Error during submit_user_token: %s", repr(e))
