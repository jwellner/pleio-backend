from core.tests.helpers.search_index_test_template import Template


class TestDiscussionSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'discussion'
    expected_hook = 'discussion.core_hooks.test_elasticsearch_index'
