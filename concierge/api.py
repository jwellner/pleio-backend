import logging

import requests
from django.conf import settings
from requests import ConnectionError as RequestConnectionError

from concierge.constances import FETCH_AVATAR_URL, FETCH_PROFILE_URL, FETCH_MAIL_PROFILE_URL
from core.lib import get_account_url
from user.models import User

logger = logging.getLogger(__name__)


def fetch_avatar(user: User):
    try:
        url = get_account_url(FETCH_AVATAR_URL.format(user.email))

        response = requests.get(url, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        }, timeout=30)

        assert response.ok, f"{response.status_code}: {response.reason}"

        return response.json()

    except RequestConnectionError as e:
        logger.warning("Error during fetch_avatar: %s; %s", e.__class__, repr(e))
        return {
            "error": str(e)
        }


def fetch_profile(user: User):
    try:
        assert user.external_id, "No external ID found yet"
        url = get_account_url(FETCH_PROFILE_URL.format(user.external_id))

        response = requests.get(url, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        }, timeout=30)

        assert response.ok, response.reason

        return response.json()

    except (AssertionError, RequestConnectionError) as e:
        logger.warning("Error during fetch_profile: %s; %s", e.__class__, repr(e))
        return {
            "error": str(e)
        }


def fetch_mail_profile(email):
    response = None
    try:
        url = get_account_url(FETCH_MAIL_PROFILE_URL.format(email))

        response = requests.get(url, headers={
            'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
            'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
        }, timeout=30)

        assert response.ok, response.reason

        return response.json()

    except (AssertionError, RequestConnectionError) as e:
        logger.warning("Error during fetch_mail_profile: %s; %s", e.__class__, repr(e))
        return {
            "error": str(e),
            "status_code": response.status_code if response else None
        }
