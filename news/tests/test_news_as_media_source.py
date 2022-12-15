from core.tests.helpers.media_entity_template import Template
from news.factories import NewsFactory
from user.factories import EditorFactory
from user.models import User


class TestNewsAsMediaSourceTestCase(Template.MediaTestCase):

    def owner_factory(self) -> User:
        return EditorFactory()

    def entity_factory(self):
        return NewsFactory(owner=self.owner,
                           title=self.TITLE,
                           rich_description=self.CONTENT)
