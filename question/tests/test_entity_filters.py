from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from question.factories import QuestionFactory


class TestTextPageFilters(Template.TestEntityFiltersTestCase):
    include_activity_query = False

    def get_subtype(self):
        return 'question'

    def subtype_factory(self, **kwargs):
        return QuestionFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
