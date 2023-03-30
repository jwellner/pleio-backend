from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from user.models import User


class Template:
    class MediaTestCase(PleioTenantTestCase):
        CONTENT = "Some demo content!"
        TITLE = "some-demo-title"
        EXTENSION = '.html'

        owner: User = None

        def owner_factory(self) -> User:
            return UserFactory()

        def entity_factory(self):  # pragma: no cover
            raise NotImplementedError()

        def setUp(self):
            super().setUp()
            self.owner = self.owner_factory()
            self.entity = self.entity_factory()
            self.expected_filename = "%s%s" % (self.TITLE, self.EXTENSION)

        def tearDown(self):
            self.entity.delete()
            self.owner.delete()
            super().tearDown()

        def test_get_media_status(self):
            self.assertTrue(self.entity.get_media_status())
            self.assertEqual(self.expected_filename, self.entity.get_media_filename())
            self.assertEqual(self.CONTENT, self.entity.get_media_content())
