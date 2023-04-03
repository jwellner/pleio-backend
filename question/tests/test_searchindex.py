from core.tests.helpers.search_index_test_template import Template


class TestQuestionUserSearchIndexTestCase(Template.SearchIndexTestTestCase):
    index_name = 'question'
    expected_hook = 'question.core_hooks.test_elasticsearch_index'
