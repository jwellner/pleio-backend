from activity.models import StatusUpdate
from blog.factories import BlogFactory
from core.constances import ACCESS_TYPE
from core.factories import GroupFactory
from core.tests.helpers.entity_filters import Template


class TestEntityFilters(Template.TestEntityFiltersTestCase):
    _group = None

    def get_subtype(self):
        return 'statusupdate'

    def tearDown(self):
        super().tearDown()

    def get_group(self):
        if not self._group:
            self._group = GroupFactory(owner=self.get_owner())

    def subtype_factory(self, **kwargs):
        return StatusUpdate.objects.create(**kwargs,
                                           group=self.get_group(),
                                           read_access=[ACCESS_TYPE.logged_in],
                                           write_access=[ACCESS_TYPE.user.format(self.get_owner().guid)])

    def reference_factory(self, **kwargs):
        return BlogFactory(**kwargs)
