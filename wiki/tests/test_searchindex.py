from core.tests.helpers.search_index_test_template import Template


class TestWikiSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'wiki'
    expected_hook = 'wiki.core_hooks.test_elasticsearch_index'
