from core.tests.helpers.media_entity_template import Template
from question.factories import QuestionFactory


class TestQuestionAsMediaSourceTestCase(Template.MediaTestCase):

    def entity_factory(self):
        return QuestionFactory(owner=self.owner,
                               title=self.TITLE,
                               rich_description=self.CONTENT)
