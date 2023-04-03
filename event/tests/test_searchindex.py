from core.tests.helpers.search_index_test_template import Template


class TestEventSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'event'
    expected_hook = 'event.core_hooks.test_elasticsearch_index'
