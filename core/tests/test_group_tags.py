from core.models import Group
from core.tests.helpers.tags_testcase import Template
from user.factories import AdminFactory
from user.models import User


class TestGroupTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Group'
    graphql_payload = 'group'
    graphql_add_mutation = 'addGroup'
    graphql_add_input = 'addGroupInput'
    graphql_update_mutation = 'editGroup'
    graphql_update_input = 'editGroupInput'
    model = Group

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'name': "Test group"
        }}

    def article_factory(self, owner: User, **kwargs):
        if 'title' in kwargs:
            kwargs['name'] = kwargs['title']
        group = super().article_factory(owner, **kwargs)
        group.join(owner, 'owner')
        return group

    def owner_factory(self):
        return AdminFactory(email="admin-owner@localhost")

    include_group_search = True
    include_site_search = True
