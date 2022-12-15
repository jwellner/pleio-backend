from blog.factories import BlogFactory
from core.tests.helpers.media_entity_template import Template


class BlogAsMediaSourceTestCase(Template.MediaTestCase):

    def entity_factory(self):
        return BlogFactory(owner=self.owner,
                           title=self.TITLE,
                           rich_description=self.CONTENT)
