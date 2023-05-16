from blog.factories import BlogFactory
from core.models import Revision
from core.post_deploy.translate_attachment_to_filefolder import migrate_revision
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMigrateRevisionAttachmentsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.inline_attachment = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                                   owner=self.owner)
        self.featured_image = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']),
                                                owner=self.owner)
        self.blog = BlogFactory(owner=self.owner,
                                rich_description=self.tiptap_attachment(self.inline_attachment),
                                featured_image=self.featured_image)
        self.revision = Revision.objects.create(author=self.owner,
                                                _container=self.blog,
                                                unchanged=self.blog.serialize())

    def tearDown(self):
        super().tearDown()

    def test_migrate_revision(self):
        migrate_revision(self.revision)

        self.assertEqual({*self.revision.attachments}, {
            self.featured_image.guid,
            self.inline_attachment.guid,
        })
