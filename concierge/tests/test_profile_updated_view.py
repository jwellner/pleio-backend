import uuid
from unittest import mock

from django.urls import resolve, ResolverMatch

from core.lib import tenant_schema
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestViewsTestCase(PleioTenantTestCase):
    PROFILE_UPDATED = '/api/profile/update/'

    def setUp(self):
        super().setUp()
        self.user = UserFactory(external_id="foo")
        self.ORIGIN_TOKEN = str(uuid.uuid4())

    def test_url_resolves(self):
        url = resolve(self.PROFILE_UPDATED)
        self.assertIsInstance(url, ResolverMatch)
        self.assertEqual(url.url_name, 'profile_updated')

    def test_visit_update_notification_requires_api_config(self):
        response = self.client.post(self.PROFILE_UPDATED)
        self.assertEqual(response.status_code, 400)

    @mock.patch('concierge.tasks.profile_updated_signal.delay')
    @mock.patch('concierge.views.ApiTokenData.assert_valid')
    def test_visit_update_notification_should_schedule_profile_update_request(self,
                                                                              mocked_assert_valid,
                                                                              mocked_profile_updated_signal):
        response = self.client.post(self.PROFILE_UPDATED,
                                    {'id': "foo"})
        self.assertEqual(response.status_code, 200)
        mocked_assert_valid.assert_called()
        mocked_profile_updated_signal.assert_called_with(tenant_schema(), self.user.guid)
