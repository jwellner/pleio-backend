import logging
from hashlib import md5

import requests
from django.conf import settings
from django.utils import timezone
from requests import ConnectionError as RequestConnectionError

from concierge.constances import FETCH_AVATAR_URL, FETCH_PROFILE_URL, FETCH_MAIL_PROFILE_URL
from core.lib import get_account_url, tenant_api_token
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


class ApiTokenData:
    def __init__(self, request):
        self.request = request
        self._data = None

    @staticmethod
    def flat_data(data):
        return {k: v for k, v in data.items()}

    @property
    def data(self):
        if not self._data:
            if self.request.method == 'POST':
                self._data = self.flat_data(self.request.POST)
            else:
                self._data = self.flat_data(self.request.GET)
        return self._data

    def assert_valid_checksum(self):
        expected_checksum = md5(tenant_api_token().encode())
        for k, v in sorted(self.data.items(), key=lambda x: [str(v).lower() for v in x]):
            if k == 'checksum':
                # Checksum is not included in the checksum.
                continue

            expected_checksum.update(k.encode())
            expected_checksum.update(v.encode())

        assert self.data.get('checksum') == expected_checksum.hexdigest()[:12], "Invalid checksum"

    def assert_valid_timestamp(self):
        assert self.data.get('timestamp'), "Timestamp is missing"

        try:
            due = timezone.now() - timezone.timedelta(minutes=int(settings.ACCOUNT_DATA_EXPIRE))
            timestamp = timezone.datetime.fromisoformat(self.data.get('timestamp', ''))
            assert timestamp > due, "Data expired"
        except ValueError:
            raise AssertionError("Invalid timestmap format.")

    def assert_valid(self):
        self.assert_valid_checksum()
        self.assert_valid_timestamp()
