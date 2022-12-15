from core.tests.helpers.media_entity_template import Template
from discussion.factories import DiscussionFactory


class TestDiscussionAsMediaSourceTestCase(Template.MediaTestCase):

    def entity_factory(self):
        return DiscussionFactory(owner=self.owner,
                                 title=self.TITLE,
                                 rich_description=self.CONTENT)
