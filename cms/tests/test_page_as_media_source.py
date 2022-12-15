from cms.factories import TextPageFactory, CampagnePageFactory
from core.tests.helpers import PleioTenantTestCase
from core.tests.helpers.media_entity_template import Template
from user.factories import EditorFactory
from user.models import User


class TextPageAsMediaSourceTestCase(Template.MediaTestCase):

    def owner_factory(self) -> User:
        return EditorFactory()

    def entity_factory(self):
        return TextPageFactory(owner=self.owner,
                               title=self.TITLE,
                               rich_description=self.CONTENT)


class CampagnePageAsMediaSourceTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = EditorFactory()
        self.entity = CampagnePageFactory(owner=self.owner)

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()
        super().tearDown()

    def test_does_not_allow_campagne_page_as_media_source(self):
        self.assertFalse(self.entity.get_media_status())
