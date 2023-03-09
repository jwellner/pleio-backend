from blog.factories import BlogFactory
from cms.factories import TextPageFactory, CampagnePageFactory
from core.tests.helpers.entity_filters import Template
from user.factories import EditorFactory


class TestTextPageFilters(Template.TestEntityFiltersTestCase):
    def get_subtype(self):
        return 'page'

    def get_owner(self):
        return EditorFactory()

    def subtype_factory(self, **kwargs):
        return TextPageFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)


class TestCampagnePageFilters(Template.TestEntityFiltersTestCase):
    include_activity_query = False

    def get_subtype(self):
        return 'page'

    def get_owner(self):
        return EditorFactory()

    def subtype_factory(self, **kwargs):
        return CampagnePageFactory(**kwargs)

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
