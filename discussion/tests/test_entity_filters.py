from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from discussion.factories import DiscussionFactory


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    def get_subtype(self):
        return 'discussion'

    def subtype_factory(self, **kwargs):
        return DiscussionFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
