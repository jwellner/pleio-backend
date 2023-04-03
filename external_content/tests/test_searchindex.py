from core.tests.helpers.search_index_test_template import Template


class TestExternalContentSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'external_content'
    expected_hook = 'external_content.core_hooks.test_elasticsearch_index'
