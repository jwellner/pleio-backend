from core.tests.helpers.tags_testcase import Template
from discussion.models import Discussion


class TestDiscussionTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Discussion'
    model = Discussion

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'title': "Test discussion",
            'subtype': 'discussion',
        }}

    include_site_search = True
    include_entity_search = True
    include_activity_search = True