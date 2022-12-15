from django.core.files.base import ContentFile

from blog.factories import BlogFactory
from core.factories import AttachmentFactory
from core.tests.helpers.media_entity_template import Template


class TestAttachmentAsMediaSourceTestCase(Template.MediaTestCase):
    EXTENSION = '.xyz'
    CONTENT = b'Binary content expected'

    def setUp(self):
        super().setUp()
        self.expected_filename = "%s%s" % (self.entity.pk, self.EXTENSION)


    def entity_factory(self):
        return AttachmentFactory(attached=BlogFactory(owner=self.owner),
                                 upload=ContentFile(self.CONTENT, "%s.xyz" % self.TITLE))
