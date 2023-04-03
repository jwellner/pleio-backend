from core.tests.helpers.search_index_test_template import Template


class TestTextpageSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'page'
    expected_hook = 'cms.core_hooks.test_elasticsearch_index'
