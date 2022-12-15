from core.tests.helpers.media_entity_template import Template
from event.factories import EventFactory


class TestEventAsMediaSourceTestCase(Template.MediaTestCase):

    def entity_factory(self):
        return EventFactory(owner=self.owner,
                            title=self.TITLE,
                            rich_description=self.CONTENT)
