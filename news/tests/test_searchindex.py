from core.tests.helpers.search_index_test_template import Template


class TestNewsSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'news'
    expected_hook = 'news.core_hooks.test_elasticsearch_index'
