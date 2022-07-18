import uuid
from unittest import mock

from django.urls import resolve, ResolverMatch

from core.lib import tenant_schema
from core.tests.helpers import PleioTenantTestCase


class TestViewsTestCase(PleioTenantTestCase):
    PROFILE_UPDATED = '/api/profile_updated/'

    def setUp(self):
        super(TestViewsTestCase, self).setUp()
        self.ORIGIN_TOKEN = str(uuid.uuid4())

    def test_url_resolves(self):
        url = resolve(self.PROFILE_UPDATED)
        self.assertIsInstance(url, ResolverMatch)
        self.assertEqual(url.url_name, 'profile_updated')

    def test_visit_update_notification_requires_api_config(self):
        response = self.client.post(self.PROFILE_UPDATED)
        self.assertEqual(response.status_code, 400)

    @mock.patch('concierge.tasks.profile_updated_signal.delay')
    def test_visit_update_notification_should_schedule_profile_update_request(self, mocked_profile_updated_signal):
        response = self.client.post(self.PROFILE_UPDATED,
                                    {'origin_token': self.ORIGIN_TOKEN})
        self.assertEqual(response.status_code, 200)
        mocked_profile_updated_signal.assert_called_with(tenant_schema(), self.ORIGIN_TOKEN)
