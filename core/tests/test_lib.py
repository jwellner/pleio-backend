import os
from unittest import mock

from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase

from core import override_local_config
from core.lib import clean_graphql_input, tenant_api_token, tenant_summary
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder


class TestCleanGraphQLInput(FastTenantTestCase):
    def test_none_values_are_removed_from_dict(self):
        d = {
            "key1": "value1",
            "key2": "",
            "key3": None,
            "key4": 0,
            "key5": False,
        }

        expected = {
            "key1": "value1",
            "key2": "",
            "key4": 0,
            "key5": False,
        }

        result = clean_graphql_input(d)
        self.assertEqual(result, expected)

    def test_empty_time_published_is_not_removed_from_dict(self):
        d = {
            "timePublished": None,
            "scheduleArchiveEntity": None,
            "scheduleDeleteEntity": None,
            "groupGuid": None
        }

        result = clean_graphql_input(d)
        self.assertEqual(result, d)


class TestTenantApiToken(FastTenantTestCase):

    @override_local_config(TENANT_API_TOKEN="exists")
    @mock.patch("core.lib.uuid.uuid4")
    def test_tenant_api_token_if_exists(self, mocked_uuid4):
        mocked_uuid4.return_value = "created-by-uuid4"
        self.assertEqual("exists", tenant_api_token())

    @override_local_config(TENANT_API_TOKEN=None)
    @mock.patch("core.lib.uuid.uuid4")
    def test_tenant_api_token_if_not_exists(self, mocked_uuid4):
        mocked_uuid4.return_value = "created-by-uuid4"

        self.assertEqual("created-by-uuid4", tenant_api_token())


class TestTenantSummary(PleioTenantTestCase):

    @override_local_config(TENANT_API_TOKEN="test",
                           DESCRIPTION="test site description.",
                           NAME="test site name")
    @override_settings(ENV='test')
    def test_without_favicon(self):
        self.assertDictEqual(tenant_summary(), {
            'api_token': 'test',
            'description': 'test site description.',
            'name': 'test site name',
            'url': 'https://tenant.fast-test.com',
        })

        self.assertDictEqual(tenant_summary(with_favicon=True), {
            'api_token': 'test',
            'description': 'test site description.',
            'name': 'test site name',
            'url': 'https://tenant.fast-test.com',
        })

    @mock.patch("base64.encodebytes")
    def test_with_favicon(self, mocked_encode_string):
        path = os.path.join(os.path.dirname(__file__), 'assets', 'favicon.ico')
        file: FileFolder = self.file_factory(path)
        mocked_encode_string.return_value = b'file contents'

        with override_local_config(FAVICON=file.download_url):
            summary = tenant_summary()
            self.assertFalse(summary.get('favicon'))
            self.assertFalse(summary.get('favicon_data'))

            summary = tenant_summary(with_favicon=True)
            self.assertEqual("favicon.ico", summary.get('favicon'))
            self.assertEqual("file contents", summary.get('favicon_data'))
