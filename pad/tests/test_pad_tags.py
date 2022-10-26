from mixer.backend.django import mixer

from core.factories import GroupFactory
from core.models import Group
from core.tests.helpers.tags_testcase import Template
from file.models import FileFolder
from user.models import User


class TestPadTagsTestCase(Template.TagsTestCaseTemplate):
    # Overrides:
    graphql_label = 'Pad'
    graphql_update_mutation = 'editPad'
    graphql_update_input = 'editPadInput'
    graphql_add_mutation = 'addPad'
    graphql_add_input = 'addPadInput'
    model = FileFolder

    _container = None

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'containerGuid': self.container.guid,
            'richDescription': '',
        }}

    @property
    def container(self):
        if not self._container:
            # required by baseclass
            self._container = GroupFactory(owner=self.owner)
        return self._container

    def article_factory(self, owner: User, **kwargs):
        kwargs.setdefault('type', FileFolder.Types.PAD)
        kwargs.setdefault('group', self.container)
        return super().article_factory(owner, **kwargs)

    include_site_search = True
    include_entity_search = True
