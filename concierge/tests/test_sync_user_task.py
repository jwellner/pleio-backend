import uuid
from unittest import mock

from django.conf import settings
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from requests import ConnectionError as RequestConnectionError

from concierge.constances import REGISTER_ORIGIN_SITE_URL
from core.lib import tenant_summary, get_account_url
from user.models import User


class TestTasksTestCase(FastTenantTestCase):

    def setUp(self):
        super(TestTasksTestCase, self).setUp()

        self.user = mixer.blend(User,
                                is_active=True,
                                external_id=256)
        self.profile = self.user.profile
        self.profile.origin_token = None
        self.profile.save()
        self.expected_uuid = uuid.uuid4()

    @mock.patch("concierge.tasks.requests.post")
    @mock.patch("concierge.tasks.uuid.uuid4")
    @override_settings(ENV='test')
    def test_user_submit_properly_formatted_request_to_concierge(self, mocked_uuid, mocked_post):
        mocked_uuid.return_value = self.expected_uuid

        from concierge.tasks import sync_user
        sync_user(self.tenant.schema_name, self.user.id)

        expected_site_config = tenant_summary()

        self.assertEqual(mocked_post.call_args.args,
                         (get_account_url(REGISTER_ORIGIN_SITE_URL.format(self.user.external_id)),))
        self.assertDictEqual(mocked_post.call_args.kwargs, {
            'data': {
                "origin_site_url": expected_site_config['url'],
                "origin_site_name": expected_site_config['name'],
                "origin_site_description": expected_site_config['description'],
                "origin_site_api_token": expected_site_config['api_token'],
                "origin_token": self.expected_uuid,
            },
            'headers': {
                "x-oidc-client-id": settings.OIDC_RP_CLIENT_ID,
                "x-oidc-client-secret": settings.OIDC_RP_CLIENT_SECRET,
            },
            'timeout': 10
        })

    @mock.patch("concierge.tasks.requests.post")
    def test_should_not_sync_inactive_users(self, mocked_post):
        self.user.is_active = False
        self.user.save()

        from concierge.tasks import sync_user
        sync_user(self.tenant.schema_name, self.user.id)

        mocked_post.assert_not_called()

    @mock.patch("concierge.tasks.requests.post")
    def test_should_not_sync_local_users(self, mocked_post):
        self.user.external_id = None
        self.user.save()

        from concierge.tasks import sync_user
        sync_user(self.tenant.schema_name, self.user.id)

        mocked_post.assert_not_called()

    @mock.patch("concierge.tasks.requests.post")
    def test_should_not_sync_synced_users(self, mocked_post):
        self.user.profile.update_origin_token(self.expected_uuid)

        from concierge.tasks import sync_user
        sync_user(self.tenant.schema_name, self.user.id)

        mocked_post.assert_not_called()

    @mock.patch('concierge.tasks.logger.warning')
    @mock.patch("concierge.tasks.requests.post")
    def test_connection_error_undoes_set_origin_token(self, mocked_post, mocked_logger):
        mocked_post.side_effect = RequestConnectionError()

        from concierge.tasks import sync_user
        sync_user(self.tenant.schema_name, self.user.id)

        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.origin_token)
