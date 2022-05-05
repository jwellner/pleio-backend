import uuid
from unittest import mock

from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from requests import ConnectionError as RequestConnectionError

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
    def test_user_submit_properly_formatted_request_to_concierge(self, mocked_uuid, mocked_post):
        mocked_uuid.return_value = self.expected_uuid

        from concierge.tasks import sync_user, settings
        sync_user(self.tenant.schema_name, self.user.id)

        mocked_post.assert_called_with(
            "{}/api/users/register_origin_site/{}".format(settings.ACCOUNT_API_URL, self.user.external_id),
            data={
                "origin_site_url": "https://{}".format(self.tenant.primary_domain),
                "origin_site_name": self.tenant.name,
                "origin_token": self.expected_uuid,
            },
            headers={
                "x-oidc-client-id": settings.OIDC_RP_CLIENT_ID,
                "x-oidc-client-secret": settings.OIDC_RP_CLIENT_SECRET,
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
