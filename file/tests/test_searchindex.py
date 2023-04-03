from core.tests.helpers.search_index_test_template import Template


class TestFileSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'file'
    expected_hook = "file.core_hooks.test_elasticsearch_index"
