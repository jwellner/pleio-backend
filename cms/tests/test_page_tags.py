from cms.models import Page
from core.tests.helpers.tags_testcase import Template
from user.factories import EditorFactory


class TestPageTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_add_mutation = 'addPage'
    graphql_add_input = 'addPageInput'
    graphql_update_mutation = 'editPage'
    graphql_update_input = 'editPageInput'
    graphql_label = 'Page'
    graphql_search_type = 'page'
    model = Page

    variables_add = {'input': {
        'title': "Test page",
        'pageType': 'text',
    }}

    def owner_factory(self):
        return EditorFactory(email="editor-owner@localhost")

    # TODO: Om 1 of andere reden is deze instabiel voor cms pagina's....
    # include_site_search = True

    include_entity_search = True

    # TODO: Om 1 of andere reden is deze instabiel voor cms pagina's....
    # include_activity_search = True
