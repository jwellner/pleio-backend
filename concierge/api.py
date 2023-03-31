import logging
import uuid
from hashlib import md5

import requests
from django.conf import settings
from django.utils import timezone
from requests import ConnectionError as RequestConnectionError

from concierge.constances import FETCH_AVATAR_URL, FETCH_PROFILE_URL, FETCH_MAIL_PROFILE_URL, REGISTER_ORIGIN_SITE_URL, UPDATE_ORIGIN_SITE_URL
from core.lib import get_account_url, tenant_api_token, tenant_summary, tenant_schema
from user.models import User

logger = logging.getLogger(__name__)


def sync_site():
    client = ConciergeClient("update_origin_site")
    return client.post(UPDATE_ORIGIN_SITE_URL, {f"origin_site_{key}": value for key, value in tenant_summary().items()})


def fetch_avatar(user: User):
    client = ConciergeClient("fetch_avatar")
    return client.fetch(FETCH_AVATAR_URL.format(user.email))


def fetch_mail_profile(email):
    client = ConciergeClient("fetch_mail_profile")
    return client.fetch(FETCH_MAIL_PROFILE_URL.format(email))


def fetch_profile(user: User):
    try:
        assert user.external_id, "No external ID found yet"

        client = ConciergeClient('fetch_profile')
        return client.fetch(FETCH_PROFILE_URL.format(user.external_id))

    except AssertionError as e:
        logger.warning("Error during fetch_profile: %s; %s", e.__class__, repr(e))
        return {
            "error": str(e),
        }


def submit_user_token(user):
    from concierge.tasks import profile_updated_signal
    client = ConciergeClient("register_origin_site")
    token = uuid.uuid4()
    user.profile.update_origin_token(token)
    url = REGISTER_ORIGIN_SITE_URL.format(user.external_id)

    data = {'origin_token': token}
    data.update({f"origin_site_{key}": value for key, value in tenant_summary().items()})

    client.post(url, data)
    if client.is_ok():
        profile_updated_signal.delay(tenant_schema(), token)
    else:
        user.profile.update_origin_token(None)
        logger.warning("Failed to sync a user origin_token for reason '%s'", client.reason)


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

            expected_checksum.update(str(k).encode())
            expected_checksum.update(str(v).encode())
        assert self.data.get('checksum') == expected_checksum.hexdigest()[:12], "Invalid checksum"

    def assert_valid_timestamp(self):
        assert self.data.get('timestamp'), "Timestamp is missing"
        try:
            due = timezone.now() - timezone.timedelta(minutes=int(settings.ACCOUNT_DATA_EXPIRE))
            timestamp = int(self.data.get('timestamp', due.timestamp()-1))
            assert timestamp > due.timestamp(), "Data expired"
        except ValueError:
            raise AssertionError("Invalid timestmap format.")

    def assert_valid(self):
        self.assert_valid_checksum()
        self.assert_valid_timestamp()


class ConciergeClient:
    def __init__(self, resource_id):
        self.method = resource_id
        self.response = None

    def fetch(self, resource):
        self.response = None
        try:
            self.response = requests.get(get_account_url(resource), headers={
                'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
                'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
            }, timeout=30)

            assert self.response.ok, self.response.reason

            return self.response.json()
        except (AssertionError, RequestConnectionError) as e:
            logger.warning("Error during api call to concierge: %s; %s; %s", e.__class__, repr(e), self.method)
            return {
                "error": str(e),
                "status_code": self.response.status_code if self.response else None
            }

    def post(self, resource, data):
        self.response = None
        try:
            self.response = requests.post(get_account_url(resource), data=data, headers={
                'x-oidc-client-id': settings.OIDC_RP_CLIENT_ID,
                'x-oidc-client-secret': settings.OIDC_RP_CLIENT_SECRET,
            }, timeout=30)

            assert self.response.ok, self.response.reason

            return self.response.json()
        except (AssertionError, RequestConnectionError) as e:
            logger.warning("Error during api call to concierge: %s; %s; %s", e.__class__, repr(e), self.method)
            return {
                "error": str(e),
                "status_code": self.response.status_code if self.response else None
            }

    def is_ok(self):
        return self.response.ok if self.response else False

    @property
    def reason(self):
        return self.response.reason or "" if self.response else ""
