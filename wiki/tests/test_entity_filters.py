from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from wiki.factories import WikiFactory


class TestTextPageFilters(Template.TestEntityFiltersTestCase):
    include_activity_query = False

    def get_subtype(self):
        return 'wiki'

    def subtype_factory(self, **kwargs):
        return WikiFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
