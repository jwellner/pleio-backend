from core.tests.helpers.tags_testcase import Template
from wiki.models import Wiki


class TestWikiTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Wiki'
    model = Wiki

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'title': "Wiki",
            'subtype': 'wiki',
        }}

    include_site_search = True
    include_entity_search = True
    include_activity_search = True