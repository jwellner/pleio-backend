import uuid
from unittest import mock

from django.test import override_settings
from mixer.backend.django import mixer

from concierge.api import submit_user_token
from core.lib import tenant_summary
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class TestApiSubmitUserTokenTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User,
                                is_active=True,
                                external_id=256)
        self.profile = self.user.profile
        self.profile.origin_token = None
        self.profile.save()
        self.expected_uuid = uuid.uuid4()

    @mock.patch("concierge.tasks.profile_updated_signal.delay")
    @mock.patch("concierge.api.ConciergeClient.post")
    @mock.patch("concierge.api.ConciergeClient.is_ok")
    @mock.patch("concierge.api.uuid.uuid4")
    @override_settings(ENV='test')
    def test_user_submit_properly_formatted_request_to_concierge(self, mocked_uuid, mocked_ok, mocked_post, mocked_profile_updated_signal):
        expected_site_config = tenant_summary()
        mocked_ok.return_value = True
        mocked_uuid.return_value = self.expected_uuid

        submit_user_token(self.user)
        self.user.profile.refresh_from_db()

        self.assertEqual(mocked_post.call_args.args,
                         ('/api/users/register_origin_site/256', {
                             "origin_site_url": expected_site_config['url'],
                             "origin_site_name": expected_site_config['name'],
                             "origin_site_description": expected_site_config['description'],
                             "origin_site_api_token": expected_site_config['api_token'],
                             "origin_token": self.expected_uuid,
                         }))
        self.assertTrue(mocked_profile_updated_signal.called)
        self.assertEqual(self.user.profile.origin_token, self.expected_uuid)
        self.assertFalse(self.mocked_log_warning.called)

    @mock.patch("concierge.api.ConciergeClient.post")
    @mock.patch("concierge.api.ConciergeClient.is_ok")
    def test_connection_error_undoes_set_origin_token(self, mocked_ok, mocked_post):
        mocked_ok.return_value = False

        submit_user_token(self.user)
        self.user.profile.refresh_from_db()

        self.assertIsNone(self.user.profile.origin_token)
        self.assertTrue(self.mocked_log_warning.called)
