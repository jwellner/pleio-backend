from unittest import mock

from core.lib import test_elasticsearch_index
from core.tests.helpers import ElasticsearchTestCase
from user.factories import UserFactory


class Template:
    class SearchIndexTestTestCase(ElasticsearchTestCase):
        index_name = None
        expected_hook = None

        def setUp(self):
            super().setUp()
            self.super_user = UserFactory(is_superadmin=True)

        def tearDown(self):
            super().tearDown()

        def test_testcase(self):
            assert self.index_name, "Add an `index_name` to the testcase."
            assert self.expected_hook, "Add an `expected_hook` for the method you expect to get called."

            self.initialize_index()
            expected_hook = mock.patch(self.expected_hook).start()

            test_elasticsearch_index(self.index_name)
            self.assertTrue(expected_hook.called)
