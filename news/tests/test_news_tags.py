from core.tests.helpers.tags_testcase import Template
from news.models import News
from user.factories import EditorFactory


class TestNewsTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'News'
    model = News

    variables_add = {'input': {
        'title': "Test newsitem",
        'subtype': 'news',
    }}

    def owner_factory(self):
        return EditorFactory(email="editor-owner@localhost")

    include_site_search = True
    include_entity_search = True
    include_activity_search = True
