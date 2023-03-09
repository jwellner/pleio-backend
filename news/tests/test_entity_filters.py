from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from news.factories import NewsFactory
from user.factories import EditorFactory


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    def get_subtype(self):
        return 'news'

    def get_owner(self):
        return EditorFactory()

    def subtype_factory(self, **kwargs):
        return NewsFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
