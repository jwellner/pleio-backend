from core.factories import GroupFactory
from core.tests.helpers.tags_testcase import Template
from file.models import FileFolder
from user.models import User
from core.tests.helpers import override_config


class TestPadTagsTestCase(Template.TagsTestCaseTemplate):
    # Overrides:
    graphql_label = 'Pad'
    graphql_search_type = 'pad'
    graphql_type = 'pad'
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

    def tearDown(self):
        super().tearDown()

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
