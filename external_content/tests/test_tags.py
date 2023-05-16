from django.utils.timezone import localtime

from core.tests.helpers.tags_testcase import Template
from external_content.factories import ExternalContentSourceFactory
from external_content.models import ExternalContent
from user.models import User


class TestExternalContentTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'ExternalContent'
    graphql_search_type = 'externalcontent'
    model = ExternalContent

    def setUp(self):
        self.source = ExternalContentSourceFactory(name="Demo")
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def article_factory(self, owner: User, **kwargs):
        kwargs.setdefault('source', self.source)
        return super().article_factory(owner, **kwargs)

    include_add_edit = False
    include_site_search = True
    include_entity_search = True
    include_activity_search = False
