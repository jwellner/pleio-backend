from core.tests.helpers.tags_testcase import Template
from task.models import Task


class TestTaskTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Task'
    model = Task

    variables_add = {'input': {
        'title': "Todo",
        'subtype': 'task',
    }}

    include_entity_search = True
