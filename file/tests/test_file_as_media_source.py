from django.core.files.base import ContentFile

from core.tests.helpers import PleioTenantTestCase
from core.tests.helpers.media_entity_template import Template
from file.factories import FolderFactory, FileFactory, PadFactory
from user.factories import UserFactory


class TestDirectoryAsMediaSource(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.entity = FolderFactory(owner=self.owner)

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()

        super().tearDown()

    def test_folder_is_not_a_media_source(self):
        self.assertFalse(self.entity.get_media_status())


class TestUploadAsMediaSource(Template.MediaTestCase):
    EXTENSION = '.xyz'
    CONTENT = b'Binary content expected'

    def setUp(self):
        super().setUp()
        self.expected_filename = "%s/%s%s" % (self.entity.guid, self.TITLE, self.EXTENSION)

    def entity_factory(self):
        return FileFactory(owner=self.owner,
                           title=self.TITLE,
                           upload=ContentFile(self.CONTENT, "%s.xyz" % self.TITLE))


class TestPadAsMediaSource(Template.MediaTestCase):
    EXTENSION = '.html'

    def entity_factory(self):
        return PadFactory(owner=self.owner,
                          title=self.TITLE,
                          rich_description=self.CONTENT)
