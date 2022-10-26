from activity.models import StatusUpdate
from core.tests.helpers.tags_testcase import Template


class TestStatusUpdateTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'StatusUpdate'
    model = StatusUpdate

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'title': "New Status",
            'subtype': 'status_update',
        }}

    include_entity_search = True
    include_activity_search = True
