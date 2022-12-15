from core.tests.helpers.media_entity_template import Template
from wiki.factories import WikiFactory


class TestWikiAsMediaSourceTestCase(Template.MediaTestCase):

    def entity_factory(self):
        return WikiFactory(owner=self.owner,
                           title=self.TITLE,
                           rich_description=self.CONTENT)
