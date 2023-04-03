from core.tests.helpers.search_index_test_template import Template


class TestUserSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'blog'
    expected_hook = 'blog.core_hooks.test_elasticsearch_index'
