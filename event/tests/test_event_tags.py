from django.utils.timezone import localtime

from core.tests.helpers.tags_testcase import Template
from event.models import Event
from user.models import User


class TestEventTagsTestCase(Template.TagsTestCaseTemplate):
    graphql_label = 'Event'
    graphql_search_type = 'event'
    model = Event

    variables_add = {'input': {
        'title': "Test event",
        'subtype': 'event',
        'startDate': str(localtime()),
        'endDate': str(localtime()),
    }}

    def article_factory(self, owner: User, **kwargs):
        kwargs.setdefault('start_date', localtime())
        kwargs.setdefault('end_date', localtime())
        return super().article_factory(owner, **kwargs)

    include_site_search = True
    include_entity_search = True
    include_activity_search = True
