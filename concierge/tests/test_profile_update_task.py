import uuid
from unittest import mock

import celery.exceptions
from mixer.backend.django import mixer

from core.lib import tenant_schema
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

    @mock.patch('concierge.tasks.fetch_profile')
    def test_profile_task_syncs_user_profile(self, mocked_request):
        from concierge.tasks import profile_updated_signal
        data = {"guid": 42,
                "username": "expected-username",
                "name": "expected-name",
                "email": "expected@email",
                "isAdmin": True,
                "isSmoothoperator": True,
                "avatarUrl": "expected-avatar_url"}
        mocked_request.return_value = data

        # When
        profile_updated_signal(tenant_schema(), self.user.id)
        self.user.refresh_from_db()

        # Then
        mocked_request.assert_called_with(self.user)
        self.assertEqual(self.user.name, data['name'])
        self.assertEqual(self.user.email, data['email'])
        self.assertEqual(self.user.picture, data['avatarUrl'])
        self.assertEqual(self.user.is_superadmin, data['isAdmin'])

    @mock.patch('concierge.tasks.fetch_profile')
    @mock.patch('logging.Logger.error')
    def test_profile_task_failure_schedules_a_retry(self, mocked_logger, mocked_request):
        from concierge.tasks import profile_updated_signal
        response = {"error": "expected-reason"}
        mocked_request.return_value = response

        try:
            # When
            profile_updated_signal(tenant_schema(), self.user.id)

            self.fail("Unexpectedly did not retry the action")  # pragma: no cover
        except celery.exceptions.Retry:
            mocked_request.assert_called()
            mocked_logger.assert_called_with('expected-reason')

    @mock.patch('concierge.tasks.fetch_profile')
    def test_profile_task_invalid_uuid_silently_ends_operation(self, mocked_request):
        from concierge.tasks import profile_updated_signal

        profile_updated_signal(tenant_schema(), uuid.uuid4())
        self.assertFalse(mocked_request.called)
