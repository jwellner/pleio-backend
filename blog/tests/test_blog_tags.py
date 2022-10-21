from blog.models import Blog
from core.tests.helpers.tags_testcase import Template


class TestBlogTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Blog'
    model = Blog

    def setUp(self):
        super().setUp()
        self.variables_add = {'input': {
            'title': "Test blog",
            'subtype': 'blog',
        }}

    include_entity_search = True
    include_activity_search = True
    include_site_search = True
