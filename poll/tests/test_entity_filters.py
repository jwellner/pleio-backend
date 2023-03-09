from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from poll.factories import PollFactory


class TestTextPageFilters(Template.TestEntityFiltersTestCase):
    include_activity_query = False

    def get_subtype(self):
        return 'poll'

    def subtype_factory(self, **kwargs):
        return PollFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
