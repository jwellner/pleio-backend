from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from event.factories import EventFactory


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    def get_subtype(self):
        return 'event'

    def subtype_factory(self, **kwargs):
        return EventFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
