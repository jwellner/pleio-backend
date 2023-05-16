from core.tests.helpers.tags_testcase import Template
from question.models import Question


class TestQuestionTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Question'
    model = Question

    variables_add = {'input': {
        'title': "Any questions?",
        'subtype': 'question',
    }}

    include_site_search = True
    include_entity_search = True
    include_activity_search = True
