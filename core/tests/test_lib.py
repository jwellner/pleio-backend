from unittest import mock

from django_tenants.test.cases import FastTenantTestCase

from core.lib import clean_graphql_input


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
            "foo": "bar",
            "timePublished": None,
        }

        result = clean_graphql_input(d)
        self.assertEqual(result, d)

    @mock.patch("core.lib.Tiptap")
    def test_external_url_check_is_not_called_if_no_rich_description(self, mock_tiptap):
        d = {
            "key:": "value"
        }

        clean_graphql_input(d)

        mock_tiptap.assert_not_called()
