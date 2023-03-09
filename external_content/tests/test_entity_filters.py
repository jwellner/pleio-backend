from blog.factories import BlogFactory
from core.tests.helpers.entity_filters import Template
from external_content.factories import ExternalContentSourceFactory, ExternalContentFactory


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    _source = None
    include_activity_query = False

    def get_subtype(self):
        return self.get_source().guid

    def get_source(self):
        if not self._source:
            self._source = ExternalContentSourceFactory()
        return self._source

    def subtype_factory(self, **kwargs):
        return ExternalContentFactory(**kwargs,
                                      source=self.get_source())

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
