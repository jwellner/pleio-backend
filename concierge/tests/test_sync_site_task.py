from unittest import mock

from django.conf import settings
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase

from core.lib import tenant_summary


class TestSyncSiteTestCase(FastTenantTestCase):

    @mock.patch("concierge.tasks.requests.post")
    @override_settings(ENV='test')
    def test_submit_properly_formatted_request_to_concierge(self, mocked_post):
        # pylint: disable=import-outside-toplevel
        from concierge.tasks import sync_site
        sync_site(self.tenant.schema_name)

        expected_site_config = tenant_summary()

        mocked_post.assert_called_with(
            "{}/api/users/update_origin_site".format(settings.ACCOUNT_API_URL),
            data={
                "origin_site_url": expected_site_config['url'],
                "origin_site_name": expected_site_config['name'],
                "origin_site_description": expected_site_config['description'],
                "origin_site_api_token": expected_site_config['api_token'],
            },
            headers={
                "x-oidc-client-id": settings.OIDC_RP_CLIENT_ID,
                "x-oidc-client-secret": settings.OIDC_RP_CLIENT_SECRET,
            })
