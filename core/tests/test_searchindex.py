from core.tests.helpers.search_index_test_template import (ElasticsearchTestCase, Template,
                                                           test_elasticsearch_index)
from core.exceptions import UnableToTestIndex


class TestUserSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'user'
    expected_hook = 'core.core_hooks._test_user_query'


class TestGroupSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'group'
    expected_hook = 'core.core_hooks._test_group_query'


class TestEdgeCaseTestCase(ElasticsearchTestCase):
    def test_testcase(self):
        with self.assertRaises(UnableToTestIndex):
            test_elasticsearch_index("foo_bar_baz")
