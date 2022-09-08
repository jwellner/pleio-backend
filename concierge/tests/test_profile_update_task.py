import uuid
from unittest import mock
from unittest.mock import Mock

from django.conf import settings
from mixer.backend.django import mixer

from concierge.constances import FETCH_PROFILE_URL
from core.lib import tenant_schema, get_account_url
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class TestTasksTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.USER_ID = 1
        self.ORIGIN_TOKEN = str(uuid.uuid4())

        # Given
        self.user = mixer.blend(User, external_id=self.USER_ID)
        self.user.profile.update_origin_token(self.ORIGIN_TOKEN)

    @mock.patch('concierge.tasks.requests.get')
    def test_profile_task_syncs_user_profile(self, mocked_request):
        from concierge.tasks import profile_updated_signal
        data = {"guid": 42,
                "username": "expected-username",
                "name": "expected-name",
                "email": "expected@email",
                "isAdmin": True,
                "isSmoothoperator": True,
                "avatarUrl": "expected-avatar_url"}
        response = Mock()
        response.ok = True
        response.json.return_value = data
        mocked_request.return_value = response

        # When
        profile_updated_signal(tenant_schema(), self.ORIGIN_TOKEN)
        self.user.refresh_from_db()

        # Then
        mocked_request.assert_called_with(get_account_url(FETCH_PROFILE_URL.format(self.USER_ID)),
                                          headers={"x-oidc-client-id": settings.OIDC_RP_CLIENT_ID,
                                                   "x-oidc-client-secret": settings.OIDC_RP_CLIENT_SECRET},
                                          timeout=30)
        self.assertEqual(self.user.name, data['name'])
        self.assertEqual(self.user.email, data['email'])
        self.assertEqual(self.user.picture, data['avatarUrl'])
        self.assertEqual(self.user.is_superadmin, data['isAdmin'])

    @mock.patch('concierge.api.requests.get')
    @mock.patch('concierge.tasks.profile_updated_signal.apply_async')
    @mock.patch('logging.Logger.error')
    def test_profile_task_failure_schedules_a_retry(self, mocked_logger, mocked_retry, mocked_request):
        from concierge.tasks import profile_updated_signal
        response = Mock()
        response.ok = False
        response.reason = 'expected-reason'
        mocked_request.return_value = response

        # When
        profile_updated_signal(tenant_schema(), self.ORIGIN_TOKEN)

        # Then
        mocked_request.assert_called()
        mocked_logger.assert_called_with('expected-reason')
        mocked_retry.assert_called()

    @mock.patch('concierge.tasks.requests.get')
    def test_profile_task_invalid_uuid_silently_ends_operation(self, mocked_get_request):
        from concierge.tasks import profile_updated_signal

        profile_updated_signal(tenant_schema(), "altered %s" % uuid.uuid4())
        mocked_get_request.asset_not_called()
